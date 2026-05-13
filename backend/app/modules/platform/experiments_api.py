"""Platform-owned experiments API implementation."""

import csv
import io
import json
import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.core.settings import get_settings
from app.modules.platform.storage import (
    create_experiment,
    get_dataset,
    get_dataset_preview,
    get_experiment,
    get_figure,
    get_metrics,
    ingest_metrics,
    list_datasets,
    list_experiments,
    list_figures,
    save_dataset,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/experiments", tags=["experiments"])

ALL_FIGURE_TYPES = [
    "line", "bar", "groupedBar", "stackedBar",
    "scatter", "bubble", "histogram", "boxplot", "violin",
    "heatmap", "radar", "roc", "pr",
]


class CreateExperimentRequest(BaseModel):
    name: str = "Untitled Experiment"
    projectId: Optional[str] = None
    planSessionId: Optional[str] = None
    planLinkId: Optional[str] = None
    description: str = ""
    tags: List[str] = Field(default_factory=list)
    status: str = "created"


class MetricEntry(BaseModel):
    key: str
    value: float
    step: Optional[int] = None
    timestamp: Optional[str] = None


class IngestMetricsRequest(BaseModel):
    metrics: List[MetricEntry]


class GenerateFigureRequest(BaseModel):
    providerName: Optional[str] = None
    model: Optional[str] = None
    preferredFigureType: Optional[str] = None
    datasetId: Optional[str] = None


class RenderFigureRequest(BaseModel):
    figureType: str
    title: str = ""
    xLabel: str = ""
    yLabel: str = ""
    caption: str = ""
    series: List[Dict[str, Any]] = Field(default_factory=list)
    heatmapData: Optional[Dict[str, Any]] = None
    datasetId: Optional[str] = None


class RecommendFiguresRequest(BaseModel):
    providerName: Optional[str] = None
    model: Optional[str] = None
    datasetId: Optional[str] = None


@router.get('/figure-types')
async def get_figure_types():
    return {"types": ALL_FIGURE_TYPES}


@router.get('')
async def list_experiments_endpoint(projectId: Optional[str] = None):
    experiments = list_experiments(project_id=projectId)
    return {"experiments": experiments, "total": len(experiments)}


@router.post('', status_code=status.HTTP_201_CREATED)
async def create_experiment_endpoint(req: CreateExperimentRequest):
    return create_experiment(req.model_dump())


@router.get('/{experiment_id}')
async def get_experiment_endpoint(experiment_id: str):
    record = get_experiment(experiment_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found")
    metrics = get_metrics(experiment_id)
    figures = list_figures(experiment_id)
    datasets = list_datasets(experiment_id)
    record['metricsCount'] = len(metrics)
    record['figuresCount'] = len(figures)
    record['datasetsCount'] = len(datasets)
    return record


@router.post('/{experiment_id}/metrics', status_code=status.HTTP_201_CREATED)
async def ingest_metrics_endpoint(experiment_id: str, req: IngestMetricsRequest):
    record = get_experiment(experiment_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found")
    count = ingest_metrics(experiment_id, [metric.model_dump() for metric in req.metrics])
    return {"ingested": count, "experimentId": experiment_id}


@router.get('/{experiment_id}/metrics')
async def get_metrics_endpoint(experiment_id: str):
    record = get_experiment(experiment_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found")
    metrics = get_metrics(experiment_id)
    return {"metrics": metrics, "total": len(metrics)}


@router.post('/{experiment_id}/datasets/upload', status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    experiment_id: str,
    file: UploadFile = File(...),
    name: str = Form('uploaded_data'),
):
    record = get_experiment(experiment_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found")

    raw_bytes = await file.read()
    if len(raw_bytes) > 50_000_000:
        raise HTTPException(status_code=400, detail='File too large (max 50MB)')

    filename = (file.filename or 'data').lower()
    try:
        if filename.endswith('.csv'):
            text = raw_bytes.decode('utf-8', errors='replace')
            reader = csv.DictReader(io.StringIO(text))
            parsed = [dict(row) for row in reader]
            for row in parsed:
                for key, value in row.items():
                    try:
                        row[key] = float(value)
                    except (ValueError, TypeError):
                        pass
            fmt = 'csv'
        elif filename.endswith('.json') or filename.endswith('.jsonl'):
            text = raw_bytes.decode('utf-8', errors='replace')
            data = json.loads(text)
            if isinstance(data, list):
                parsed = data
            elif isinstance(data, dict):
                parsed = [data]
            else:
                parsed = [{'value': data}]
            fmt = 'json'
        else:
            raise HTTPException(status_code=400, detail='Unsupported format. Use CSV or JSON.')
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(exc)[:200]}")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(exc)[:200]}")

    if not parsed:
        raise HTTPException(status_code=400, detail='File contains no data rows')

    meta = save_dataset(experiment_id, name, fmt, raw_bytes, parsed)
    return meta


@router.get('/{experiment_id}/datasets')
async def list_datasets_endpoint(experiment_id: str):
    datasets = list_datasets(experiment_id)
    return {"datasets": datasets, "total": len(datasets)}


@router.get('/datasets/{dataset_id}')
async def get_dataset_endpoint(dataset_id: str):
    dataset = get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found")
    return dataset


@router.get('/datasets/{dataset_id}/preview')
async def get_dataset_preview_endpoint(dataset_id: str):
    dataset = get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found")
    preview = get_dataset_preview(dataset_id)
    return {"datasetId": dataset_id, "rows": preview, "total": len(preview), "columns": dataset.get('columns', [])}


@router.post('/{experiment_id}/figures/generate', status_code=status.HTTP_201_CREATED)
async def generate_figure_endpoint(experiment_id: str, req: GenerateFigureRequest):
    record = get_experiment(experiment_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found")
    try:
        from app.services.figure_service import generate_figure
        data_override = None
        if req.datasetId:
            preview = get_dataset_preview(req.datasetId)
            if preview:
                data_override = preview
        settings = get_settings()
        provider_name = req.providerName or settings.get_active_provider()
        model = req.model or settings.get_active_model(provider_name)
        artifact = generate_figure(
            experiment_id=experiment_id,
            provider_name=provider_name,
            model=model,
            preferred_figure_type=req.preferredFigureType,
            data_override=data_override,
        )
        return artifact
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error('Figure generation failed: %s', exc, exc_info=True)
        error_msg = str(exc)
        code = 400 if 'API key' in error_msg or 'not configured' in error_msg else 500
        raise HTTPException(status_code=code, detail=f"Figure generation failed: {error_msg}")


@router.post('/{experiment_id}/figures/render', status_code=status.HTTP_201_CREATED)
async def render_figure_endpoint(experiment_id: str, req: RenderFigureRequest):
    record = get_experiment(experiment_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found")
    if req.figureType not in ALL_FIGURE_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported figure type. Use one of: {ALL_FIGURE_TYPES}")
    try:
        from app.services.figure_service import generate_figure
        user_spec = {
            'figureType': req.figureType,
            'title': req.title,
            'xLabel': req.xLabel,
            'yLabel': req.yLabel,
            'caption': req.caption,
            'series': req.series,
            'heatmapData': req.heatmapData,
        }
        data_override = None
        if req.datasetId:
            preview = get_dataset_preview(req.datasetId)
            if preview:
                data_override = preview
        artifact = generate_figure(
            experiment_id=experiment_id,
            user_spec=user_spec,
            data_override=data_override or [{'_': 1}],
        )
        return artifact
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error('Figure rendering failed: %s', exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Figure rendering failed: {str(exc)}")


@router.get('/{experiment_id}/figures')
async def list_figures_endpoint(experiment_id: str):
    figures = list_figures(experiment_id)
    return {"figures": figures, "total": len(figures)}


@router.get('/figures/{figure_id}/png')
async def get_figure_png(figure_id: str):
    figure = get_figure(figure_id)
    if not figure:
        raise HTTPException(status_code=404, detail=f"Figure '{figure_id}' not found")
    png_path = figure.get('pathPng')
    if not png_path or not os.path.isfile(png_path):
        raise HTTPException(status_code=404, detail='PNG file not found')
    return FileResponse(png_path, media_type='image/png', filename=f'{figure_id}.png')


@router.get('/figures/{figure_id}/pdf')
async def get_figure_pdf(figure_id: str):
    figure = get_figure(figure_id)
    if not figure:
        raise HTTPException(status_code=404, detail=f"Figure '{figure_id}' not found")
    pdf_path = figure.get('pathPdf')
    if not pdf_path or not os.path.isfile(pdf_path):
        raise HTTPException(status_code=404, detail='PDF file not found')
    return FileResponse(pdf_path, media_type='application/pdf', filename=f'{figure_id}.pdf')


@router.get('/figures/{figure_id}/code')
async def get_figure_code(figure_id: str):
    figure = get_figure(figure_id)
    if not figure:
        raise HTTPException(status_code=404, detail=f"Figure '{figure_id}' not found")
    code_path = figure.get('pathCode')
    if not code_path or not os.path.isfile(code_path):
        raise HTTPException(status_code=404, detail='Code file not found for this figure')
    with open(code_path, 'r') as handle:
        code = handle.read()
    return {'figureId': figure_id, 'code': code, 'language': 'python'}


@router.get('/figures/{figure_id}/download/code.py')
async def download_figure_code(figure_id: str):
    figure = get_figure(figure_id)
    if not figure:
        raise HTTPException(status_code=404, detail=f"Figure '{figure_id}' not found")
    code_path = figure.get('pathCode')
    if not code_path or not os.path.isfile(code_path):
        raise HTTPException(status_code=404, detail='Code file not found')
    return FileResponse(code_path, media_type='text/x-python', filename=f'{figure_id}_plot.py')


@router.post('/{experiment_id}/figures/recommend')
async def recommend_figures_endpoint(experiment_id: str, req: RecommendFiguresRequest):
    record = get_experiment(experiment_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found")
    try:
        from app.services.figure_service import recommend_figures
        data_override = None
        if req.datasetId:
            preview = get_dataset_preview(req.datasetId)
            if preview:
                data_override = preview
        recommendations = recommend_figures(
            experiment_id=experiment_id,
            provider_name=req.providerName,
            model=req.model,
            data_override=data_override,
        )
        return {'experimentId': experiment_id, 'recommendations': recommendations}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error('Figure recommendation failed: %s', exc, exc_info=True)
        error_msg = str(exc)
        code = 400 if 'API key' in error_msg or 'not configured' in error_msg else 500
        raise HTTPException(status_code=code, detail=f'Recommendation failed: {error_msg}')
