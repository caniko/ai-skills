#!/usr/bin/env nu

skillnet --config ./skillnet.toml --catalog-config ./skillnet.catalog.toml --allow-dirty-destination sync pull --all --then-push
