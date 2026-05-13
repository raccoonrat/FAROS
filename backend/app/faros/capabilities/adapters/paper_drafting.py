import os
from typing import Any, Dict

from app.faros.capabilities.base import BaseCapability
from app.faros.models.artifact import ArtifactRecord
from app.faros.models.capability import CapabilityResult
from app.faros.models.execution import ExecutionContext
from app.modules.paper.service import generate_paper
from app.modules.paper.storage import create_paper, create_paper_zip, get_paper_latex_dir, list_paper_files


class PaperDraftingCapability(BaseCapability):
    capability_id = "paper_drafting"
    description = "Generate a paper artifact using the current paper generation module."

    def execute(self, context: ExecutionContext, inputs: Dict[str, Any]) -> CapabilityResult:
        binding = context.get_binding() or context.get_binding(self.capability_id)
        provider_name = binding.provider if binding else inputs.get("providerName", "moonshot")
        model = binding.model if binding and binding.model else inputs.get("model", "moonshot-v1-8k")

        selected_candidate = inputs.get("selectedCandidate") or {}
        title = inputs.get("title") or selected_candidate.get("title") or inputs.get("seedQuery") or "FAROS Draft"
        notes_parts = []
        if selected_candidate:
            notes_parts.append(f"Selected idea candidate: {selected_candidate.get('title', 'N/A')}")
            notes_parts.append(f"Problem: {selected_candidate.get('problem', '')}")
            notes_parts.append(f"Key insight: {selected_candidate.get('keyInsight', '')}")
        if inputs.get("notes"):
            notes_parts.append(inputs["notes"])

        record = create_paper(
            {
                "title": title,
                "paperType": inputs.get("paperType", "algorithm"),
                "targetVenue": inputs.get("targetVenue", "generic"),
                "planLinkId": inputs.get("planLinkId"),
                "projectId": inputs.get("projectId"),
                "experimentIds": inputs.get("experimentIds", []),
                "figureIds": inputs.get("figureIds", []),
                "runIds": inputs.get("runIds", []),
                "providerName": provider_name,
                "model": model,
                "notes": "\n".join(part for part in notes_parts if part),
            }
        )

        paper = generate_paper(record["id"])
        latex_dir = get_paper_latex_dir(record["id"])
        zip_path = create_paper_zip(record["id"])
        pdf_path = os.path.join(latex_dir, "main.pdf")
        files = list_paper_files(record["id"])

        artifacts = [
            ArtifactRecord(
                id=f"{context.run_id}:{self.capability_id}:paper",
                type="paper_record",
                uri=f"paper://{record['id']}",
                producer=self.capability_id,
                summary=f"Paper {record['id']} generated for venue {paper.get('targetVenue', 'generic')}",
                metadata={"paperId": record["id"], "status": paper.get("status")},
            ),
            ArtifactRecord(
                id=f"{context.run_id}:{self.capability_id}:latex",
                type="latex_project",
                uri=latex_dir,
                producer=self.capability_id,
                summary=f"LaTeX project with {len(files)} entries",
                metadata={"paperId": record["id"], "fileCount": len(files)},
            ),
        ]
        if zip_path:
            artifacts.append(
                ArtifactRecord(
                    id=f"{context.run_id}:{self.capability_id}:zip",
                    type="latex_zip",
                    uri=zip_path,
                    producer=self.capability_id,
                    summary="Downloadable LaTeX bundle",
                    metadata={"paperId": record["id"]},
                )
            )
        if os.path.isfile(pdf_path):
            artifacts.append(
                ArtifactRecord(
                    id=f"{context.run_id}:{self.capability_id}:pdf",
                    type="paper_pdf",
                    uri=pdf_path,
                    producer=self.capability_id,
                    summary="Compiled paper PDF",
                    metadata={"paperId": record["id"]},
                )
            )

        return CapabilityResult(
            status="completed" if paper.get("status") == "completed" else paper.get("status", "failed"),
            outputs={
                "paperId": record["id"],
                "paperTitle": paper.get("title"),
                "paperStatus": paper.get("status"),
                "paperVenue": paper.get("targetVenue"),
                "pdfAvailable": paper.get("pdfAvailable", False),
                "paperFileCount": len(files),
            },
            artifacts=artifacts,
            events=[
                {
                    "level": "info",
                    "message": f"Paper drafting completed for {record['id']}",
                }
            ],
        )
