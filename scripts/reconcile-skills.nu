#!/usr/bin/env nu

# Reconcile host skill directories into this repository's skill mirror.
#
# Plan:
# 1. Read global skills directly from the live host roots:
#    - /home/can/.agents/skills
#    - /home/can/.claude/skills
#    - /home/can/.codex/skills
# 2. Read project skills from the maintained absolute repo-root list below.
# 3. Treat each actual skill directory as the merge unit.
#    Claude/Codex `.system/*` children are flattened into normal skill names;
#    `.system` itself is not copied because it is a container, not a skill.
# 4. When the same skill exists in more than one source, choose the source tree
#    with the newest file mtime.
# 5. Exact newest-time ties are allowed only when the tied directory contents
#    are identical. Same timestamp with different content is ambiguous and
#    stops the run.
# 6. Rebuild `global/` and every `projects/<name>/` target as flat sets of
#    skill directories.
# 7. Sync each reconciled set back to `.agents/skills` and `.claude/skills`.
#    Then remove the stale `.codex/skills` copy; Codex reads from
#    `.agents/skills`. If a project `.codex` directory becomes empty, remove it.

const global_sources = [
    { label: "agents", path: "/home/can/.agents/skills", priority: 3 },
    { label: "claude", path: "/home/can/.claude/skills", priority: 2 },
    { label: "codex", path: "/home/can/.codex/skills", priority: 1 },
]

const supported_projects = [
    { name: "SynDB", path: "~/canix/Projects/SynDB", extra_sources: [] },
    { name: "SynDB-dep-machete-udeps", path: "~/canix/Projects/SynDB-dep-machete-udeps", extra_sources: [] },
    { name: "ai-yolo-nix", path: "~/canix/Projects/ai-yolo-nix", extra_sources: [] },
    { name: "canix", path: "~/canix/Projects/canix", extra_sources: [] },
    { name: "codex", path: "~/canix/Projects/codex", extra_sources: [] },
    { name: "fragpipe-mcp", path: "~/canix/Projects/fragpipe-mcp", extra_sources: [] },
    { name: "goose", path: "~/canix/Projects/upstream/goose", extra_sources: [] },
    { name: "mempalace", path: "~/canix/Projects/upstream/mempalace", extra_sources: [
        { label: "integration", rel: "integrations", priority: 1 },
    ] },
    { name: "nix-crossbow", path: "~/canix/Projects/nix-crossbow", extra_sources: [] },
    { name: "plinth", path: "~/canix/Projects/solo/plinth", extra_sources: [] },
    { name: "regicide", path: "~/canix/Projects/solo/game-dev/regicide", extra_sources: [
        { label: "vendor-fragpipe", rel: "vendor/fragpipe/skills", priority: 2 },
        { label: "vendor-thespis", rel: "vendor/thespis/.agents/skills", priority: 1 },
    ] },
    { name: "rs-modde", path: "~/canix/Projects/rs-modde", extra_sources: [] },
    { name: "rs_bouldy", path: "~/canix/Projects/rs_bouldy", extra_sources: [] },
    { name: "syndb-morphometry-rollout", path: "~/canix/Projects/.codex-worktrees/syndb-morphometry-rollout", extra_sources: [] },
]

const project_skill_sources = [
    { label: "agents", rel: ".agents/skills", priority: 6 },
    { label: "claude", rel: ".claude/skills", priority: 5 },
    { label: "codex", rel: ".codex/skills", priority: 4 },
    { label: "root-skills", rel: "skills", priority: 3 },
    { label: "codex-plugin", rel: ".codex-plugin/skills", priority: 2 },
    { label: "claude-plugin", rel: ".claude-plugin/skills", priority: 1 },
]

def fail [message: string] {
    print --stderr $message
    exit 1
}

def dir_newest_mtime [dir: string] {
    let rows = (^find $dir -type f -printf "%T@ %p\n" | complete)

    if $rows.exit_code != 0 {
        fail $"failed to inspect source directory: ($dir)\n($rows.stderr)"
    }

    let stamps = (
        $rows.stdout
        | lines
        | where {|line| ($line | str length) > 0 }
        | each {|line| ($line | split row " " | first | into float) }
    )

    if ($stamps | is-empty) {
        0.0
    } else {
        $stamps | math max
    }
}

def dir_content_signature [dir: string] {
    let result = (
        ^bash -c 'cd "$1" || exit 1
if ! find . -type f -print -quit | grep -q .; then
  exit 0
fi
find . -type f -print0 | sort -z | xargs -0 sha256sum' bash $dir
        | complete
    )

    if $result.exit_code != 0 {
        fail $"failed to hash source directory: ($dir)\n($result.stderr)"
    }

    $result.stdout
}

def candidate_from_dir [entry: record, label: string, priority: int] {
    let skill = ($entry.name | path basename)
    {
        skill: $skill,
        source: $label,
        priority: $priority,
        path: $entry.name,
        newest_mtime: (dir_newest_mtime $entry.name),
        content_signature: (dir_content_signature $entry.name),
    }
}

def regular_skill_dirs [root: string, label: string, priority: int] {
    ls -a $root
    | where type == dir
    | where {|entry| ($entry.name | path basename) != ".system" }
    | each {|entry| candidate_from_dir $entry $label $priority }
}

def system_skill_dirs [root: string, label: string, priority: int] {
    let system_root = ($root | path join ".system")

    if not ($system_root | path exists) {
        []
    } else {
        ls -a $system_root
        | where type == dir
        | each {|entry| candidate_from_dir $entry $label $priority }
    }
}

def source_candidates [source: record] {
    if not ($source.path | path exists) {
        []
    } else {
        (regular_skill_dirs $source.path $source.label $source.priority)
        | append (system_skill_dirs $source.path $"($source.label)-system" $source.priority)
    }
}

def target_candidates [sources: list] {
    $sources
    | each {|source| source_candidates $source }
    | flatten
}

def choose_latest [candidates: list] {
    $candidates
    | group-by skill
    | transpose skill candidates
    | each {|group|
        let sorted = ($group.candidates | sort-by --reverse newest_mtime priority)
        let winner = ($sorted | first)
        let tied = (
            $sorted
            | where {|candidate| $candidate.newest_mtime == $winner.newest_mtime }
        )

        if (($tied | length) > 1) {
            let tied_signatures = ($tied | get content_signature | uniq)

            if (($tied_signatures | length) > 1) {
                let details = (
                    $tied
                    | each {|candidate| $"  - ($candidate.skill): ($candidate.source) ($candidate.path), mtime=($candidate.newest_mtime)" }
                    | str join "\n"
                )
                fail $"ambiguous newest source for skill `($group.skill)`:\n($details)"
            }
        }

        $winner
        | insert candidate_count ($group.candidates | length)
        | reject content_signature
    }
}

def copy_skill [candidate: record, output: string] {
    let dest = ($output | path join $candidate.skill)
    mkdir $output
    rm -rf $dest

    let result = (^cp -a $candidate.path $dest | complete)
    if $result.exit_code != 0 {
        fail $"failed to copy ($candidate.path) to ($dest)\n($result.stderr)"
    }
}

def copy_skill_dir [source: string, output: string] {
    let dest = ($output | path join ($source | path basename))
    mkdir $output
    rm -rf $dest

    let result = (^cp -a $source $dest | complete)
    if $result.exit_code != 0 {
        fail $"failed to copy ($source) to ($dest)\n($result.stderr)"
    }
}

def sync_one [staging: string, sync_path: string] {
    let sync_staging = $"($sync_path).reconcile-tmp"
    rm -rf $sync_staging
    mkdir $sync_staging

    for entry in (ls -a $staging | where type == dir | sort-by name) {
        copy_skill_dir $entry.name $sync_staging
    }

    rm -rf $sync_path
    mkdir ($sync_path | path dirname)
    mv $sync_staging $sync_path
}

def remove_stale_codex_skills [skills_path: string] {
    if ($skills_path | path exists) {
        rm -rf $skills_path
    }

    let codex_dir = ($skills_path | path dirname)

    if ($codex_dir | path exists) {
        let remaining = (ls -a $codex_dir | where name !~ '/\\.\\.?$')
        if ($remaining | is-empty) {
            rm -rf $codex_dir
        }
    }
}

def sync_back [staging: string, sync_paths: list, stale_codex_skill_paths: list] {
    for sync_path in $sync_paths {
        sync_one $staging $sync_path
    }

    for path in $stale_codex_skill_paths {
        remove_stale_codex_skills $path
    }
}

def write_manifest [choices: list, output: string, sources: list] {
    let manifest = ($output | path join "RECONCILIATION.md")
    let rows = (
        $choices
        | sort-by skill
        | each {|choice|
            $"| `($choice.skill)` | `($choice.source)` | `($choice.path)` | `($choice.newest_mtime)` | ($choice.candidate_count) |"
        }
        | str join "\n"
    )

    let body = [
        "# Skill Reconciliation",
        "",
        "Generated by `scripts/reconcile-skills.nu`.",
        "",
        "## Rule",
        "",
        "Generated outputs are flat sets of skill directories. Candidates are read from live source roots, not from existing repository mirrors. Claude/Codex `.system/*` children are flattened into normal global skills.",
        "",
        "When the same skill exists in more than one source, the source tree with the newest file mtime wins. Exact newest-time ties are accepted only when the tied directory contents are identical.",
        "",
        "After reconciliation, the selected skills are synchronized back to `.agents/skills` and `.claude/skills`. Stale `.codex/skills` copies are removed because Codex reads from `.agents/skills`; a `.codex` directory is removed only when that leaves it empty.",
        "",
        "## Sources",
        "",
        ...($sources | each {|source| $"- ($source.label): `($source.path)`" }),
        "",
        "## Choices",
        "",
        "| Skill | Selected Source | Selected Path | Newest Mtime | Candidates |",
        "|---|---|---|---:|---:|",
        $rows,
        "",
    ] | str join "\n"

    $body | save --force $manifest
}

def reconcile_target [
    name: string
    output: string
    sources: list
    sync_paths: list
    stale_codex_skill_paths: list
    --dry-run
] {
    let existing_sources = ($sources | where {|source| $source.path | path exists })

    if ($existing_sources | is-empty) {
        print --stderr $"warning: no existing skill source directories for target `($name)`"
        return
    }

    let candidates = (target_candidates $existing_sources)

    if ($candidates | is-empty) {
        print --stderr $"warning: no skill directories found for target `($name)`"
        return
    }

    let choices = (choose_latest $candidates)

    if $dry_run {
        print $"# ($name) -> ($output)"
        print (
            $choices
            | sort-by skill
            | select skill source path newest_mtime candidate_count
            | table
        )
        print $"sync-back: ($sync_paths | str join ', ')"
        if not ($stale_codex_skill_paths | is-empty) {
            print $"remove-stale-codex-skills: ($stale_codex_skill_paths | str join ', ')"
        }
        return
    }

    let staging = $"($output).reconcile-tmp"
    rm -rf $staging
    mkdir $staging

    for choice in ($choices | sort-by skill) {
        copy_skill $choice $staging
    }

    write_manifest $choices $staging $existing_sources
    sync_back $staging $sync_paths $stale_codex_skill_paths

    rm -rf $output
    mv $staging $output

    print $"reconciled (($choices | length)) skills into ($output)"
}

def project_sources [project: record] {
    let standard_sources = (
        $project_skill_sources
        | each {|source|
            {
                label: $source.label,
                path: ($project.path | path join $source.rel),
                priority: $source.priority,
            }
        }
    )

    let extra_sources = (
        $project.extra_sources
        | each {|source|
            {
                label: $source.label,
                path: ($project.path | path join $source.rel),
                priority: $source.priority,
            }
        }
    )

    $standard_sources
    | append $extra_sources
}

def main [
    --target: string = "all" # all, global, or one supported project name
    --dry-run
] {
    if $target == "all" or $target == "global" {
        reconcile_target "global" "global" $global_sources ["/home/can/.agents/skills", "/home/can/.claude/skills"] ["/home/can/.codex/skills"] --dry-run=$dry_run
    }

    if $target != "global" {
        let projects = if $target == "all" {
            $supported_projects
        } else {
            $supported_projects | where name == $target
        }

        if ($projects | is-empty) {
            fail $"unknown target `($target)`. Use `all`, `global`, or one of: ($supported_projects | get name | str join ', ')"
        }

        for project in $projects {
            reconcile_target $project.name ($"projects/($project.name)") (project_sources $project) [($project.path | path join ".agents/skills"), ($project.path | path join ".claude/skills")] [($project.path | path join ".codex/skills")] --dry-run=$dry_run
        }
    }
}
