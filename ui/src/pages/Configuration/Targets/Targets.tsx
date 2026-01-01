import React, { useEffect, useState } from 'react';
import { targetsApi } from '../../../services/api';
import { Target } from '../../../types';
import { Card, Button, Badge } from '../../../components/common';
import styles from './Targets.module.css';

export const Targets: React.FC = () => {
  const [targets, setTargets] = useState<Target[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadTargets();
  }, []);

  const loadTargets = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await targetsApi.list();
      setTargets(data);
    } catch (err: any) {
      setError(err.detail || 'Failed to load targets');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className={styles.loading}>Loading targets...</div>;
  }

  return (
    <div className={styles.targets}>
      <div className={styles.header}>
        <h2>Targets</h2>
        <Button onClick={() => alert('Target creation form coming soon')}>
          + Add Target
        </Button>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      <div className={styles.list}>
        {targets.length === 0 ? (
          <Card className={styles.empty}>
            <p>No targets found. Create your first target to get started.</p>
          </Card>
        ) : (
          targets.map((target) => (
            <Card key={target.id} className={styles.targetCard}>
              <div className={styles.targetHeader}>
                <h3>{target.name}</h3>
                <div className={styles.badges}>
                  <Badge variant="info">{target.deployment_type}</Badge>
                  <Badge variant={target.status === 'Active' ? 'success' : 'neutral'}>
                    {target.status}
                  </Badge>
                </div>
              </div>
              <div className={styles.targetDetails}>
                {target.hostname && <div><strong>Hostname:</strong> {target.hostname}</div>}
                {target.ip_address && <div><strong>IP:</strong> {target.ip_address}</div>}
                <div><strong>Tier:</strong> {target.tier}</div>
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

