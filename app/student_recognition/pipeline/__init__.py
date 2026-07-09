"""Pipeline layer: orchestration and scheduling only.

Responsibilities (constitution §2 / §13 / §14): ``state_machine`` validates
transitions, ``recognition_job`` orchestrates a job through its layers, and
``recognition_worker`` schedules jobs. These modules DELEGATE all algorithms to
the capture / drafts / review / grading_bridge modules; they contain no OMR,
image-processing or grading code.
"""
