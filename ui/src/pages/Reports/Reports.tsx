import React, { useState } from 'react';
import { Card, Button } from '../../components/common';
import styles from './Reports.module.css';

export const Reports: React.FC = () => {
  const [selectedReport, setSelectedReport] = useState<string | null>(null);

  const reportTypes = [
    { id: 'compliance', name: 'Compliance Report', description: 'Overall JDK compliance status across all projects', icon: '📊' },
    { id: 'non-compliant', name: 'Non-Compliant Applications', description: 'List of applications with non-compliant JDK versions', icon: '❌' },
    { id: 'exemptions', name: 'Exemptions Report', description: 'Applications with active exemptions', icon: '✅' },
    { id: 'trends', name: 'Compliance Trends', description: 'Historical compliance trends over time', icon: '📈' },
  ];

  const handleGenerateReport = (reportId: string) => {
    setSelectedReport(reportId);
    // TODO: Implement report generation API
    alert(`Generating ${reportTypes.find(r => r.id === reportId)?.name}. This feature will be available soon.`);
  };

  const handleExport = (format: 'pdf' | 'excel') => {
    if (!selectedReport) {
      alert('Please generate a report first');
      return;
    }
    // TODO: Implement export API
    alert(`Exporting report as ${format.toUpperCase()}. This feature will be available soon.`);
  };

  return (
    <div className={styles.reports}>
      <div className={styles.header}>
        <h1>Compliance Reports</h1>
        <p>Generate and view JDK compliance reports</p>
      </div>

      <div className={styles.reportsGrid}>
        {reportTypes.map((report) => (
          <Card key={report.id} className={styles.reportCard}>
            <div className={styles.reportIcon}>{report.icon}</div>
            <h3>{report.name}</h3>
            <p>{report.description}</p>
            <Button
              onClick={() => handleGenerateReport(report.id)}
              variant={selectedReport === report.id ? 'primary' : 'secondary'}
              fullWidth
            >
              Generate Report
            </Button>
          </Card>
        ))}
      </div>

      {selectedReport && (
        <Card className={styles.reportViewer}>
          <div className={styles.viewerHeader}>
            <h2>
              {reportTypes.find(r => r.id === selectedReport)?.name} - Preview
            </h2>
            <div className={styles.viewerActions}>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => handleExport('pdf')}
              >
                Export PDF
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => handleExport('excel')}
              >
                Export Excel
              </Button>
            </div>
          </div>
          <div className={styles.reportContent}>
            <div className={styles.placeholder}>
              <p>Report preview will appear here</p>
              <p className={styles.note}>
                Report generation and viewing will be available soon.
              </p>
            </div>
          </div>
        </Card>
      )}

      <Card className={styles.recentReports}>
        <h2>Recent Reports</h2>
        <div className={styles.reportsList}>
          <div className={styles.emptyState}>
            <p>No reports generated yet. Generate a report to see it here.</p>
          </div>
        </div>
      </Card>
    </div>
  );
};

