import React from 'react';
import styles from './TextArea.module.css';

export interface TextAreaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  fullWidth?: boolean;
}

export const TextArea = React.forwardRef<HTMLTextAreaElement, TextAreaProps>(
  ({ label, error, fullWidth = false, className = '', ...props }, ref) => {
    return (
      <div className={`${styles.wrapper} ${fullWidth ? styles.fullWidth : ''}`}>
        {label && (
          <label htmlFor={props.id} className={styles.label}>
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          className={`${styles.textarea} ${error ? styles.error : ''} ${className}`}
          {...props}
        />
        {error && <span className={styles.errorText}>{error}</span>}
      </div>
    );
  }
);

TextArea.displayName = 'TextArea';
