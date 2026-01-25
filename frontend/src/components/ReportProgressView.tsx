/**
 * Component for displaying report generation progress with detailed step tracking.
 */

interface ReportProgressViewProps {
  currentStep: number;
  stepName: string;
  currentProgress: number;
  totalProgress: number;
  progressMessage: string;
  query: string;
}

const STEP_NAMES = [
  "Selecting Top Papers",
  "Generating Paper Cards",
  "Creating Report Outline",
  "Writing Sections",
  "Auditing Citations",
  "Writing Introduction & Conclusion",
  "Assembling Report",
  "Final Quality Check",
];

export function ReportProgressView({
  currentStep,
  stepName,
  currentProgress,
  totalProgress,
  progressMessage,
  query,
}: ReportProgressViewProps) {
  const totalSteps = 8;
  const overallProgress = ((currentStep + (totalProgress > 0 ? currentProgress / totalProgress : 0)) / totalSteps) * 100;

  return (
    <div className="report-progress-view">
      <div className="report-progress-header">
        <h2>Generating Report: {query}</h2>
      </div>

      <div className="progress-overview">
        <div className="overall-progress">
          <div className="progress-label">
            <span>Overall Progress</span>
            <span className="progress-percentage">{Math.round(overallProgress)}%</span>
          </div>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${overallProgress}%` }}
            />
          </div>
        </div>
      </div>

      <div className="current-step-info">
        <div className="step-indicator">
          <div className="step-number">Step {currentStep + 1} of {totalSteps}</div>
          <div className="step-name">{stepName || STEP_NAMES[currentStep] || "Processing..."}</div>
        </div>
        
        {totalProgress > 0 && (
          <div className="step-progress">
            <div className="progress-label">
              <span>{progressMessage || `Processing ${currentProgress} of ${totalProgress}...`}</span>
              <span className="progress-count">{currentProgress} / {totalProgress}</span>
            </div>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${(currentProgress / totalProgress) * 100}%` }}
              />
            </div>
          </div>
        )}
        
        {totalProgress === 0 && progressMessage && (
          <div className="step-message">
            {progressMessage}
          </div>
        )}
      </div>

      <div className="steps-list">
        <h3>Report Generation Steps</h3>
        <div className="steps-container">
          {STEP_NAMES.map((name, index) => {
            const isCompleted = index < currentStep;
            const isCurrent = index === currentStep;
            const isPending = index > currentStep;

            return (
              <div
                key={index}
                className={`step-item ${isCompleted ? 'completed' : ''} ${isCurrent ? 'current' : ''} ${isPending ? 'pending' : ''}`}
              >
                <div className="step-item-indicator">
                  {isCompleted ? (
                    <span className="step-checkmark">✓</span>
                  ) : isCurrent ? (
                    <span className="step-number-badge">{index + 1}</span>
                  ) : (
                    <span className="step-number-badge pending">{index + 1}</span>
                  )}
                </div>
                <div className="step-item-content">
                  <div className="step-item-name">{name}</div>
                  {isCurrent && totalProgress > 0 && (
                    <div className="step-item-progress">
                      {currentProgress} / {totalProgress}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
