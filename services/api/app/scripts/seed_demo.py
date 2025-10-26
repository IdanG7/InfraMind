"""Seed demo data"""

import random
from datetime import datetime, timedelta

from ..models.orm import Pipeline, Run, Step
from ..storage.postgres import SessionLocal, init_db
from ..ml.trainer import train_model


def generate_demo_data(num_runs: int = 50) -> None:
    """Generate synthetic demo runs"""
    print(f"Generating {num_runs} demo runs...")

    init_db()
    session = SessionLocal()

    try:
        # Create demo pipeline
        pipeline = Pipeline(
            name="demo/example-app",
            repo="https://github.com/demo/example-app",
        )
        session.add(pipeline)
        session.flush()

        # Generate runs with varying configs
        for i in range(num_runs):
            # Vary parameters
            concurrency = random.choice([2, 4, 6, 8])
            cpu_req = random.choice([2, 4, 6, 8])
            mem_req_gb = random.choice([4, 8, 16, 32])

            # Simulate duration based on params (inverse relationship with resources)
            base_duration = 600  # 10 minutes base
            duration_factor = (16 / cpu_req) * (32 / mem_req_gb) * (8 / concurrency)
            duration_s = base_duration * duration_factor + random.gauss(0, 30)
            duration_s = max(60, duration_s)  # At least 1 minute

            started_at = datetime.utcnow() - timedelta(days=num_runs - i)

            run = Run(
                pipeline_id=pipeline.id,
                run_id=f"demo-run-{i:03d}",
                status="success",
                duration_s=duration_s,
                started_at=started_at,
                finished_at=started_at + timedelta(seconds=duration_s),
                image=f"builder:v{random.choice(['1.0', '1.1', '2.0'])}",
                node=f"node-{random.randint(1, 5)}",
                cpu_req=cpu_req,
                mem_req_gb=mem_req_gb,
                concurrency=concurrency,
                artifact_bytes=random.randint(100_000_000, 500_000_000),
                branch="main",
                commit=f"abc{i:03d}",
                git="https://github.com/demo/example-app",
            )
            session.add(run)
            session.flush()

            # Generate steps
            stages = [
                ("checkout", 5, 100),
                ("configure", 15, 200),
                ("build", 180, 2000),
                ("test", 120, 1500),
                ("package", 30, 500),
            ]

            for stage_name, base_dur, base_mem in stages:
                step_dur = base_dur * (duration_factor * 0.5 + 0.5) + random.gauss(0, 5)
                step_dur = max(1, step_dur)

                start_ts = started_at
                end_ts = start_ts + timedelta(seconds=step_dur)

                step = Step(
                    run_id=run.run_id,
                    stage=stage_name,
                    step=stage_name,
                    span_id=f"span-{i}-{stage_name}",
                    start_ts=start_ts,
                    end_ts=end_ts,
                    cpu_time_s=step_dur * 0.8,
                    rss_max_bytes=int(base_mem * 1024 * 1024 * random.uniform(0.8, 1.2)),
                    io_r_bytes=random.randint(1_000_000, 100_000_000),
                    io_w_bytes=random.randint(100_000, 10_000_000),
                    cache_hits=random.randint(50, 200),
                    cache_misses=random.randint(10, 50),
                )
                session.add(step)

                started_at = end_ts

        session.commit()
        print(f"Created {num_runs} demo runs")

    finally:
        session.close()


def main() -> None:
    """Main entry point"""
    generate_demo_data(50)
    print("\nTraining initial model...")
    result = train_model("demo/example-app")
    print(f"Model trained: {result}")
    print("\nDemo data ready! Open Grafana at http://localhost:3000")


if __name__ == "__main__":
    main()
