# Implementation Plan: AI Data Quality Intelligence Platform

## Overview

Incremental implementation starting with infrastructure and core backend, then the ML pipeline, then the frontend, and finally integration and deployment. Each task builds on the previous, with property-based tests placed close to the code they validate.

## Tasks

- [x] 1. Project scaffolding and infrastructure setup
  - Create the full directory structure: `frontend/`, `backend/`, `ml_pipeline/`, `streaming/`, `docker/`, `deployment/`
  - Write `docker/docker-compose.yml` starting all services: PostgreSQL, MongoDB, Redis, Kafka, Zookeeper, MinIO (S3-compatible)
  - Write `backend/requirements.txt` and `ml_pipeline/requirements.txt` with all pinned dependencies
  - Write `frontend/package.json` with all dependencies (React 18, TypeScript, Vite, ShadCN, Tailwind, Recharts, Framer Motion, TanStack Query, Zustand, fast-check, Vitest)
  - Add `/health` stub endpoints to each service
  - _Requirements: 17.1, 17.2, 17.4, 17.5_

- [x] 2. Backend: Core configuration, database connections, and auth
  - [x] 2.1 Implement `backend/app/core/config.py` using `pydantic-settings` to load all env vars (DB URLs, JWT secret, OpenAI key, S3 config, Redis URL)
    - _Requirements: 17.4_
  - [x] 2.2 Implement `backend/app/db/postgres.py` with async SQLAlchemy 2.0 engine and session factory; write Alembic migration for all tables (users, datasets, dataset_versions, jobs, alerts)
    - _Requirements: 1.8, 12.1_
  - [x] 2.3 Implement `backend/app/db/mongo.py` with Motor async client and `backend/app/db/redis.py` with aioredis client
    - _Requirements: 13.3_
  - [x] 2.4 Implement `backend/app/core/security.py`: bcrypt password hashing (cost factor 12), JWT creation and verification using `python-jose`
    - _Requirements: 1.1, 1.8_
  - [x]* 2.5 Write property test for JWT round-trip: for any user_id and role, creating then decoding a token returns the original claims
    - **Property 9: JWT authentication validity**
    - **Validates: Requirements 1.1, 1.3**
  - [x]* 2.6 Write property test for bcrypt: for any password string, the hash starts with `$2b$12$` indicating cost factor 12
    - **Validates: Requirements 1.8**
  - [x] 2.7 Implement `backend/app/api/v1/auth.py`: POST `/api/v1/auth/login`, POST `/api/v1/auth/refresh`, POST `/api/v1/auth/logout`; enforce RBAC via FastAPI dependency
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  - [x]* 2.8 Write unit tests for auth endpoints: valid login returns JWT, invalid credentials return error without revealing which field is wrong, expired token returns 401
    - _Requirements: 1.1, 1.2, 1.4_

- [x] 3. Backend: Dataset ingestion API
  - [x] 3.1 Implement `backend/app/api/v1/datasets.py`: POST `/api/v1/datasets` (multipart upload), GET `/api/v1/datasets`, GET `/api/v1/datasets/{id}`, DELETE `/api/v1/datasets/{id}`
    - Validate file format (CSV, JSON, XLSX only) and size (≤ 2 GB)
    - Upload raw file to MinIO/S3 and create Dataset record in PostgreSQL
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.8_
  - [x]* 3.2 Write property test for file format validation: for any file extension not in {csv, json, xlsx}, the upload endpoint returns HTTP 422
    - **Validates: Requirements 2.5**
  - [x] 3.3 Implement `backend/app/api/v1/datasets.py`: GET `/api/v1/datasets/{id}/versions`, POST `/api/v1/datasets/{id}/baseline`
    - _Requirements: 8.3, 12.2, 12.3_
  - [x] 3.4 Implement `backend/app/api/v1/jobs.py`: POST `/api/v1/jobs` (submit pipeline job with config), GET `/api/v1/jobs/{id}`, GET `/api/v1/jobs/{id}/status`
    - Enqueue Celery task on job creation; return job ID immediately
    - _Requirements: 2.8_

- [x] 4. Backend: Rate limiting, alerts, and admin API
  - [x] 4.1 Implement Redis-based rate limiting middleware: 100 requests/minute per authenticated user; return HTTP 429 with `Retry-After` header when exceeded
    - _Requirements: 15.4_
  - [x]* 4.2 Write property test for rate limiting: for any user sending 101 requests in 60 seconds, the 101st returns HTTP 429
    - **Property 10: Rate limiting enforcement**
    - **Validates: Requirements 15.4**
  - [x] 4.3 Implement `backend/app/api/v1/alerts.py`: GET `/api/v1/alerts`, PATCH `/api/v1/alerts/{id}/acknowledge`
    - _Requirements: 16.3, 16.4_
  - [x] 4.4 Implement `backend/app/api/v1/admin.py`: GET/POST/PATCH `/api/v1/admin/users` (Admin role required); return 403 for non-Admin users
    - _Requirements: 1.5, 1.6, 1.7_
  - [x]* 4.5 Write unit test: non-Admin user accessing admin endpoints returns HTTP 403
    - _Requirements: 1.7_

- [x] 5. Checkpoint — Backend API
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. ML Pipeline: Processing engine abstraction and data profiler
  - [x] 6.1 Implement `ml_pipeline/pipeline/engine.py`: define `ProcessingEngine` Protocol with all required methods; implement `get_engine()` factory that returns SparkEngine if Spark is available, else DaskEngine
    - _Requirements: 13.1_
  - [x] 6.2 Implement `ml_pipeline/pipeline/spark_engine.py`: SparkSession initialization, `read_dataset()` (CSV/JSON/XLSX from S3), `write_dataset()` (CSV/JSON/XLSX to S3)
    - _Requirements: 13.1, 13.4, 13.6_
  - [x] 6.3 Implement `ml_pipeline/pipeline/dask_engine.py`: Dask DataFrame equivalents of read/write operations as fallback
    - _Requirements: 13.1_
  - [x] 6.4 Implement `ml_pipeline/pipeline/profiler.py`: compute schema detection, missing value percentages, descriptive statistics (mean, median, std, min, max, quartiles), cardinality, top-N frequencies, and correlation matrix
    - _Requirements: 3.1, 3.2, 3.4, 3.5_
  - [x]* 6.5 Write property test for data profiler: for any DataFrame with known shape, the profile's row_count and column_count match the DataFrame dimensions; missing_pct for each column equals known_missing / total_rows * 100
    - **Validates: Requirements 3.1, 10.2**

- [x] 7. ML Pipeline: Quality scoring
  - [x] 7.1 Implement `ml_pipeline/pipeline/scorer.py`: compute Completeness (% non-missing cells), Consistency (% values conforming to detected dtype), Accuracy (% non-outlier values); compute overall score as (C + Co + A) / 3
    - _Requirements: 10.1, 10.2, 10.3, 10.4_
  - [x]* 7.2 Write property test for quality score bounds: for any DataFrame, all three component scores and the overall score are in [0, 100]
    - **Property 1: Data Quality Score bounds invariant**
    - **Validates: Requirements 10.1, 10.2, 10.3, 10.4**
  - [x]* 7.3 Write property test for completeness formula: for any DataFrame with known total cells T and missing cells M, Completeness = (T - M) / T * 100
    - **Property 2: Completeness score matches missing value count**
    - **Validates: Requirements 10.2, 4.1**

- [x] 8. ML Pipeline: Missing value handling
  - [x] 8.1 Implement `ml_pipeline/pipeline/imputer.py`: implement KNN Imputation, MICE (IterativeImputer), Regression Imputation, and mean/median/mode strategies; implement `auto_select()` that evaluates strategies via cross-validation and picks the lowest-error method per column; flag columns with >80% missing
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  - [ ]* 8.2 Write property test for imputation: for any DataFrame and any supported imputation strategy, after imputation the column contains zero null/NaN/empty values
    - **Property 3: Imputation eliminates missing values**
    - **Validates: Requirements 4.1, 4.2**
  - [ ]* 8.3 Write edge-case test: a column with exactly 81% missing values is flagged and not imputed; a column with 79% missing is imputed normally
    - **Validates: Requirements 4.5**

- [ ] 9. ML Pipeline: Outlier detection
  - [ ] 9.1 Implement `ml_pipeline/pipeline/outlier_detector.py`: implement Isolation Forest, Z-score, IQR, and DBSCAN detectors; implement ensemble method that flags a point only when ≥2 methods agree; record which method(s) flagged each point; implement removal, capping (winsorization), and median imputation handling strategies
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  - [ ]* 9.2 Write property test for ensemble agreement: for any dataset, every point flagged by the ensemble method is also flagged by at least 2 of the 4 individual methods
    - **Property 4: Outlier detection ensemble agreement**
    - **Validates: Requirements 5.4**
  - [ ]* 9.3 Write unit tests for outlier handling strategies: removal reduces row count, capping clips values to [p1, p99], median imputation replaces outlier with column median
    - _Requirements: 5.3_

- [ ] 10. ML Pipeline: Data transformation
  - [ ] 10.1 Implement `ml_pipeline/pipeline/transformer.py`: StandardScaler and RobustScaler with stored fit parameters; One-Hot Encoding and Label Encoding with stored mappings; polynomial features (degree 2); interaction terms; date/time decomposition (year, month, day, hour, weekday)
    - _Requirements: 7.1, 7.2, 7.3, 7.4_
  - [ ]* 10.2 Write property test for scaling round-trip: for any numeric column and any scaler, `inverse_transform(transform(x))` equals `x` within tolerance 1e-6
    - **Property 5: Transformation round-trip (scaling)**
    - **Validates: Requirements 7.1, 7.3**
  - [ ]* 10.3 Write property test for label encoding round-trip: for any categorical column, `decode(encode(x))` equals `x` exactly
    - **Property 6: Encoding round-trip (label encoding)**
    - **Validates: Requirements 7.2, 7.3**

- [ ] 11. ML Pipeline: Anomaly detection (Autoencoder)
  - [ ] 11.1 Implement `ml_pipeline/pipeline/anomaly_detector.py`: Keras Autoencoder model (encoder-decoder architecture); train on dataset; compute reconstruction error per record; flag records above 95th percentile threshold; support retraining on new data
    - _Requirements: 6.1, 6.2, 6.3, 6.4_
  - [ ]* 11.2 Write unit test: after training on clean data, injecting known anomalous records results in those records having reconstruction error above the 95th percentile threshold
    - _Requirements: 6.1, 6.2_

- [ ] 12. ML Pipeline: Drift detection
  - [ ] 12.1 Implement `ml_pipeline/pipeline/drift_detector.py`: KS test for numeric columns, chi-squared test for categorical columns; flag columns with p-value < 0.05; return drift report with statistics per column
    - _Requirements: 8.1, 8.2_
  - [ ]* 12.2 Write property test for drift self-consistency: for any dataset compared against itself as baseline, all KS test p-values are > 0.05 (no drift detected)
    - **Property 11: Drift detection symmetry**
    - **Validates: Requirements 8.1**
  - [ ]* 12.3 Write unit test: two datasets drawn from clearly different distributions (e.g., N(0,1) vs N(10,1)) produce p-value < 0.05 for the numeric column
    - _Requirements: 8.1, 8.2_

- [ ] 13. Checkpoint — ML Pipeline core
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 14. ML Pipeline: AI Advisor and report generation
  - [ ] 14.1 Implement `ml_pipeline/ai/advisor.py`: OpenAI API client wrapper; `infer_column_semantics(profile)` → returns semantic type + confidence per column; `generate_narrative(issues, fixes)` → plain-English report text; `suggest_transformations(profile)` → transformation recommendations; `explain_anomalies(anomaly_report)` → plain-English anomaly explanations; graceful degradation when API is unavailable
    - _Requirements: 3.6, 3.7, 4.6, 5.6, 7.5, 9.3, 9.4_
  - [ ] 14.2 Implement `ml_pipeline/pipeline/report_generator.py`: assemble full Report document from all pipeline stage outputs; generate PDF using ReportLab; upload PDF to S3; write Report document to MongoDB
    - _Requirements: 9.1, 9.2, 9.5_
  - [ ]* 14.3 Write property test for report serialization round-trip: for any Report object, `deserialize(serialize(report))` equals the original report
    - **Property 8: Report serialization round-trip**
    - **Validates: Requirements 9.1**

- [ ] 15. ML Pipeline: Celery worker and full pipeline orchestration
  - [ ] 15.1 Implement `backend/app/tasks/pipeline_task.py`: Celery task that orchestrates all 12 pipeline stages in sequence; updates job progress (0–100) in Redis after each stage; handles errors by setting job status to FAILED; creates DatasetVersion record on completion; triggers alert creation if quality score < threshold
    - _Requirements: 2.8, 9.5, 10.6, 12.1, 13.2, 16.1_
  - [ ]* 15.2 Write property test for version monotonicity: after submitting N jobs for a dataset, the version numbers are exactly [1, 2, ..., N] with no gaps
    - **Property 7: Dataset versioning monotonicity**
    - **Validates: Requirements 12.1, 12.2**
  - [ ]* 15.3 Write property test for quality score alert: for any computed score below the configured threshold, an alert record exists in the database for that job
    - **Property 12: Quality score alert threshold**
    - **Validates: Requirements 10.6, 16.1**

- [ ] 16. Backend: Download and export API
  - [ ] 16.1 Implement `backend/app/api/v1/datasets.py`: GET `/api/v1/datasets/{id}/download?format=csv|xlsx|json` — generate presigned S3 URL for the cleaned dataset file in the requested format
    - _Requirements: 14.1, 14.3, 14.4_
  - [ ] 16.2 Implement `backend/app/api/v1/reports.py`: GET `/api/v1/reports/{id}` (JSON), GET `/api/v1/reports/{id}/download` (PDF presigned URL)
    - _Requirements: 9.2, 14.2, 14.4_

- [ ] 17. Streaming ingestor
  - [ ] 17.1 Implement `streaming/ingestor.py`: Kafka consumer using `confluent-kafka`; accumulate records into micro-batches (configurable window 1–60 seconds); submit each batch as a pipeline job via internal API call; support JSON and CSV-encoded messages
    - _Requirements: 2.6, 11.5_

- [ ] 18. Checkpoint — Backend + Pipeline integration
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 19. Frontend: Project setup and layout
  - [ ] 19.1 Initialize Vite + React 18 + TypeScript project; configure Tailwind CSS with custom theme (deep blue `#0F172A` background, teal `#14B8A6` accents); install and configure ShadCN UI components; set up Framer Motion; configure TanStack Query client and Zustand store
    - _Requirements: 11.6, 11.7_
  - [ ] 19.2 Implement `frontend/src/components/layout/`: `Sidebar` (navigation links), `Header` (user menu, notification bell, theme toggle), `ThemeProvider` (dark/light mode with localStorage persistence)
    - _Requirements: 11.6_
  - [ ] 19.3 Implement `frontend/src/api/`: axios instance with JWT interceptor (attach token, handle 401 refresh); TanStack Query hooks for all API endpoints
    - _Requirements: 1.3, 1.4_

- [ ] 20. Frontend: Authentication pages
  - [ ] 20.1 Implement `frontend/src/pages/AuthPage.tsx`: login form with React Hook Form + Zod validation; call POST `/api/v1/auth/login`; store JWT in memory (not localStorage); redirect to dashboard on success
    - _Requirements: 1.1, 1.2_
  - [ ] 20.2 Implement Zustand auth store: `useAuthStore` with `user`, `token`, `login()`, `logout()` actions; protected route wrapper component that redirects unauthenticated users to `/login`
    - _Requirements: 1.3, 1.4_

- [ ] 21. Frontend: Dashboard page
  - [ ] 21.1 Implement `frontend/src/pages/DashboardPage.tsx`: Data Quality Score gauge (Recharts RadialBarChart with animation); recent jobs list; active alerts panel; quick stats cards (total datasets, jobs today, avg quality score)
    - _Requirements: 10.5, 11.4, 16.3_
  - [ ] 21.2 Implement WebSocket hook `useJobUpdates(jobId)`: connect to `/ws/jobs/{job_id}`; update job progress in Zustand store; fall back to 5-second polling if WebSocket fails
    - _Requirements: 11.5_
  - [ ] 21.3 Implement `frontend/src/components/features/AlertsPanel.tsx`: list active alerts with type icon, message, timestamp; acknowledge button calls PATCH `/api/v1/alerts/{id}/acknowledge`
    - _Requirements: 16.3, 16.4_

- [ ] 22. Frontend: Dataset management pages
  - [ ] 22.1 Implement `frontend/src/pages/DatasetsPage.tsx`: dataset list table (name, format, row count, quality score, created date); file upload dialog with drag-and-drop (react-dropzone), format validation, progress bar
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_
  - [ ] 22.2 Implement `frontend/src/pages/DatasetDetailPage.tsx`: dataset metadata header; tabbed view with tabs: Profile, Versions, Jobs; version history timeline component
    - _Requirements: 11.8, 12.2, 12.4_
  - [ ] 22.3 Implement `frontend/src/components/features/DataProfileView.tsx`: missing values heatmap (Recharts HeatMap or custom SVG grid); column statistics table; correlation matrix heatmap; AI semantic inference badges with confidence scores
    - _Requirements: 3.3, 3.7, 11.1_

- [ ] 23. Frontend: Job detail and visualization pages
  - [ ] 23.1 Implement `frontend/src/pages/JobDetailPage.tsx`: pipeline stage progress stepper; before-vs-after comparison charts (box plots for numeric columns, bar charts for categorical); outlier scatter plot with highlighted anomalous points; real-time progress bar
    - _Requirements: 11.2, 11.3, 11.5_
  - [ ] 23.2 Implement `frontend/src/pages/ReportPage.tsx`: AI narrative text display; issues found list; fixes applied list; recommendations list; download PDF button; Data Quality Score breakdown (three gauge charts for Completeness, Consistency, Accuracy)
    - _Requirements: 9.1, 9.2, 10.5_
  - [ ]* 23.3 Write Vitest unit tests for QualityScoreGauge component: renders correct percentage value, applies correct color (green ≥70, yellow 50–69, red <50)
    - _Requirements: 10.5_

- [ ] 24. Frontend: Natural language interface
  - [ ] 24.1 Implement `frontend/src/components/features/NLQueryBar.tsx`: text input accepting natural language commands (e.g., "Clean this dataset and prepare for ML"); submit to POST `/api/v1/jobs` with `nl_query` field; display interpreted actions before execution
    - _Requirements: 9.3_

- [ ] 25. Checkpoint — Frontend
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 26. Backend: WebSocket support and OpenAPI docs
  - [ ] 26.1 Implement WebSocket endpoint `GET /ws/jobs/{job_id}` in FastAPI: subscribe to Redis pub/sub channel for job progress updates; push status JSON to connected clients; close connection on job completion or failure
    - _Requirements: 11.5_
  - [ ] 26.2 Configure FastAPI OpenAPI documentation at `/docs` and `/redoc`; add response schemas and examples for all endpoints
    - _Requirements: 15.5_

- [ ] 27. Deployment configuration
  - [ ] 27.1 Write `Dockerfile` for each service: `frontend/Dockerfile` (multi-stage: build with Node, serve with nginx), `backend/Dockerfile` (Python 3.11 slim), `ml_pipeline/Dockerfile` (Python 3.11 with PySpark), `streaming/Dockerfile` (Python 3.11)
    - _Requirements: 17.1_
  - [ ] 27.2 Write `deployment/k8s/` manifests: Deployment + Service for frontend, backend, worker, streaming; StatefulSet for PostgreSQL; Deployment for Redis and MongoDB; ConfigMap for non-secret config; Secret template for sensitive values
    - _Requirements: 17.3, 17.4_
  - [ ] 27.3 Add `/health` endpoint implementations to all services returning `{"status": "ok"}` with HTTP 200
    - _Requirements: 17.5_

- [ ] 28. Final checkpoint — Full integration
  - Ensure all tests pass, docker-compose up starts all services cleanly, and the frontend can complete a full dataset upload → pipeline job → report view flow. Ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Each task references specific requirements for traceability
- Property tests use Hypothesis (Python) with `max_examples=100` and fast-check (TypeScript)
- Checkpoints ensure incremental validation at key milestones
- The OpenAI API key must be set in environment variables; the pipeline degrades gracefully without it
