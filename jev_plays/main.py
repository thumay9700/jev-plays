"""
CLI entry point for running Jev-powered game agents.
Supports Pokémon Red and future games in a unified interface.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path

from .core.jev_client import JevDecisionClient
from .core.telemetry import TelemetryTracker
from .games.pokemon_red.agent import PokemonRedAgent
from .games.pokemon_red.game import PokemonRedGame

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("jev-plays")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run autonomous game agents powered by TypeSafe AI's Jev System One model."
    )
    parser.add_argument(
        "--game",
        type=str,
        default="pokemon_red",
        choices=["pokemon_red"],
        help="Game environment to launch (default: pokemon_red).",
    )
    parser.add_argument(
        "--rom",
        type=str,
        default=os.environ.get("POKEMON_ROM_PATH", "PokemonRed.gb"),
        help="Path to the game ROM file (default: PokemonRed.gb).",
    )
    parser.add_argument(
        "--speed",
        type=int,
        default=int(os.environ.get("EMULATION_SPEED", "0")),
        help="Emulation speed multiplier (0 = unlimited / maximum speed, 1 = 1x real-time 60fps).",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run emulator headlessly without an SDL2 window.",
    )
    parser.add_argument(
        "--mock-jev",
        action="store_true",
        help="Use local mock System One engine (no API key needed, zero API cost).",
    )
    parser.add_argument(
        "--overlay-output",
        type=str,
        default="hud_overlay.json",
        help="Path to write real-time HUD telemetry for OBS / video overlays (default: hud_overlay.json).",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=0,
        help="Maximum agent actions before terminating (0 = run indefinitely until completion).",
    )
    return parser.parse_args()


def run_pokemon_red(args, telemetry: TelemetryTracker, client: JevDecisionClient):
    rom_path = Path(args.rom)
    if not rom_path.exists():
        logger.error(
            f"\n[!] ROM file not found: {rom_path.resolve()}\n"
            "Please place your legally obtained 'PokemonRed.gb' in the project directory\n"
            "or specify its location with --rom <path/to/rom>."
        )
        sys.exit(1)

    game = PokemonRedGame(
        rom_path=rom_path,
        headless=args.headless,
        emulation_speed=args.speed,
    )
    agent = PokemonRedAgent(
        client=client,
        telemetry=telemetry,
        memory_reader=game.pyboy.memory,
    )

    logger.info("Initializing Game Boy boot sequence...")
    game.reset()
    logger.info("Starting autonomous Jev gameplay loop. Press Ctrl+C to stop.")

    step_count = 0
    start_time = time.time()

    try:
        while not game.is_done():
            action = agent.step()
            game.step(action)
            step_count += 1

            if args.max_steps > 0 and step_count >= args.max_steps:
                logger.info(f"Reached max steps limit ({args.max_steps}).")
                break

    except KeyboardInterrupt:
        logger.info("\nExecution paused by user.")
    finally:
        total_time = time.time() - start_time
        game.close()

        logger.info("\n" + "=" * 50)
        logger.info("SESSION METRICS & TELEMETRY SUMMARY")
        logger.info("=" * 50)
        stats = telemetry.get_stats_summary()
        logger.info(f"Total Playback Time:  {total_time:.1f}s")
        logger.info(f"Total Steps Executed: {step_count}")
        logger.info(f"Total Jev API Calls:  {stats['total_calls']}")
        logger.info(f"Average Latency:      {stats['avg_latency_ms']} ms")
        logger.info(f"P95 Latency:          {stats['p95_latency_ms']} ms")
        logger.info(f"Min / Max Latency:    {stats['min_latency_ms']}ms / {stats['max_latency_ms']}ms")
        logger.info(f"Estimated Cost:       ${stats['estimated_cost_usd']:.4f}")
        logger.info("=" * 50 + "\n")


def main():
    args = parse_args()
    telemetry = TelemetryTracker(overlay_file=args.overlay_output)
    client = JevDecisionClient(
        telemetry=telemetry,
        mock_mode=args.mock_jev,
    )

    if args.game == "pokemon_red":
        run_pokemon_red(args, telemetry, client)
    else:
        logger.error(f"Unsupported game: {args.game}")
        sys.exit(1)


if __name__ == "__main__":
    main()
