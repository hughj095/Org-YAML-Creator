"""CLI entrypoint for telemetry-to-yaml pipeline."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from telemetry_to_yaml.generator.yaml_writer import build_manifest, write_manifest_yaml
from telemetry_to_yaml.parser.analyzer import analyze_telemetry
from telemetry_to_yaml.providers.postgres import PostgresProvider, ProviderConnectionError


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate dbt semantic YAML from metadata and query telemetry")
    parser.add_argument("--provider", choices=["postgres"], default="postgres")
    parser.add_argument("--output", default="semantic_models.yml")
    parser.add_argument("--limit", type=int, default=1_000, help="Max number of query-log rows to analyze")
    parser.add_argument("--dotenv", default=None, help="Optional path to .env file")
    parser.add_argument("--log-level", default="INFO")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    if args.provider != "postgres":
        raise ValueError(f"Unsupported provider: {args.provider}")

    provider = PostgresProvider.from_env(dotenv_path=args.dotenv)

    try:
        table_metadata = provider.extract_table_metadata()
        query_logs = provider.extract_query_logs(limit=args.limit)
    except ProviderConnectionError as exc:
        logging.error("Pipeline failed due to provider connection issue: %s", exc)
        return 1

    parsed = analyze_telemetry(table_metadata, query_logs)
    manifest = build_manifest(table_metadata, parsed)

    output = Path(args.output)
    write_manifest_yaml(manifest, str(output))
    logging.info("Wrote semantic YAML to %s", output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
