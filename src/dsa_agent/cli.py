from __future__ import annotations

from .orchestrator import DsaLearningAgent


def main() -> None:
    agent = DsaLearningAgent()
    print("AI DSA Learning Agent prototype. Gõ 'exit' để thoát.")

    while True:
        try:
            message = input("\nSinh viên> ").strip()
        except EOFError:
            break

        if message.lower() in {"exit", "quit", "thoát"}:
            break

        if not message:
            continue

        turn = agent.handle(message)
        print(f"\nAgent [{turn.intent.value}]> {turn.response}")


if __name__ == "__main__":
    main()
