"""Initial schema for Phase 2.1

Revision ID: 001_initial
Revises: 
Create Date: 2026-02-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # code_projects
    op.create_table(
        'code_projects',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('repo_path', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('task_goal', sa.Text(), nullable=True),
        sa.Column('constraints', sa.Text(), nullable=True),
        sa.Column('expected_commands', sa.String(), nullable=True),
        sa.Column('acceptance_criteria', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_code_projects_name', 'code_projects', ['name'])

    # repo_contexts
    op.create_table(
        'repo_contexts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('repo_path', sa.String(), nullable=False),
        sa.Column('file_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('chunk_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_lines', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('languages', sa.String(), nullable=True),
        sa.Column('scan_duration_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['code_projects.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_repo_contexts_project_id', 'repo_contexts', ['project_id'])

    # code_sessions
    op.create_table(
        'code_sessions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=True),
        sa.Column('repo_context_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('goal', sa.Text(), nullable=False),
        sa.Column('provider_name', sa.String(), nullable=False, server_default='moonshot'),
        sa.Column('model', sa.String(), nullable=False, server_default='moonshot-v1-8k'),
        sa.Column('max_candidates', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('max_iterations', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('constraints', sa.Text(), nullable=True),
        sa.Column('target_files', sa.String(), nullable=True),
        sa.Column('current_step', sa.String(), nullable=True),
        sa.Column('iteration_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('selected_candidate_id', sa.String(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('duration_sec', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['code_projects.id']),
        sa.ForeignKeyConstraint(['repo_context_id'], ['repo_contexts.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_code_sessions_project_id', 'code_sessions', ['project_id'])

    # code_candidates
    op.create_table(
        'code_candidates',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('approach', sa.Text(), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('patch', sa.Text(), nullable=False, server_default=''),
        sa.Column('files_modified', sa.String(), nullable=True),
        sa.Column('testing_notes', sa.Text(), nullable=True),
        sa.Column('run_commands', sa.String(), nullable=True),
        sa.Column('score_correctness', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('score_completeness', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('score_efficiency', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('score_readability', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('score_safety', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('overall_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('rank', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['code_sessions.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_code_candidates_session_id', 'code_candidates', ['session_id'])

    # code_jobs
    op.create_table(
        'code_jobs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('candidate_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('mode', sa.String(), nullable=False, server_default='quick'),
        sa.Column('command', sa.String(), nullable=False),
        sa.Column('env_vars', sa.String(), nullable=True),
        sa.Column('cwd_rel', sa.String(), nullable=True),
        sa.Column('timeout_sec', sa.Integer(), nullable=False, server_default='300'),
        sa.Column('workspace_path', sa.String(), nullable=True),
        sa.Column('pid', sa.Integer(), nullable=True),
        sa.Column('exit_code', sa.Integer(), nullable=True),
        sa.Column('stdout_path', sa.String(), nullable=True),
        sa.Column('stderr_path', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('duration_sec', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['code_sessions.id']),
        sa.ForeignKeyConstraint(['candidate_id'], ['code_candidates.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_code_jobs_session_id', 'code_jobs', ['session_id'])
    op.create_index('ix_code_jobs_candidate_id', 'code_jobs', ['candidate_id'])

    # eval_reports
    op.create_table(
        'eval_reports',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('job_id', sa.String(), nullable=False),
        sa.Column('candidate_id', sa.String(), nullable=True),
        sa.Column('syntax_valid', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('lint_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('risk_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('lint_issues', sa.String(), nullable=True),
        sa.Column('test_passed', sa.Boolean(), nullable=True),
        sa.Column('test_output', sa.Text(), nullable=True),
        sa.Column('test_duration_ms', sa.Integer(), nullable=True),
        sa.Column('scores', sa.String(), nullable=True),
        sa.Column('overall_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('grade', sa.String(), nullable=False, server_default='F'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['code_jobs.id']),
        sa.ForeignKeyConstraint(['candidate_id'], ['code_candidates.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_eval_reports_job_id', 'eval_reports', ['job_id'], unique=True)
    op.create_index('ix_eval_reports_candidate_id', 'eval_reports', ['candidate_id'])

    # trace_logs
    op.create_table(
        'trace_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('job_id', sa.String(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('step', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('data', sa.String(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['code_jobs.id']),
        sa.ForeignKeyConstraint(['session_id'], ['code_sessions.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_trace_logs_job_id', 'trace_logs', ['job_id'])
    op.create_index('ix_trace_logs_session_id', 'trace_logs', ['session_id'])

    # artifacts
    op.create_table(
        'artifacts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=True),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('job_id', sa.String(), nullable=True),
        sa.Column('kind', sa.String(), nullable=False),
        sa.Column('path', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('checksum', sa.String(), nullable=True),
        sa.Column('mime_type', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['code_jobs.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_artifacts_project_id', 'artifacts', ['project_id'])
    op.create_index('ix_artifacts_session_id', 'artifacts', ['session_id'])
    op.create_index('ix_artifacts_job_id', 'artifacts', ['job_id'])


def downgrade() -> None:
    op.drop_table('artifacts')
    op.drop_table('trace_logs')
    op.drop_table('eval_reports')
    op.drop_table('code_jobs')
    op.drop_table('code_candidates')
    op.drop_table('code_sessions')
    op.drop_table('repo_contexts')
    op.drop_table('code_projects')
