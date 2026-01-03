import React from 'react';
import styles from './Select.module.css';

export interface SelectOption {
  value: string | number;
  label: string;
}

export interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'placeholder'> {
  label?: string;
  error?: string;
  fullWidth?: boolean;
  options: SelectOption[];
  placeholder?: string;
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, fullWidth = false, options, className = '', ...props }, ref) => {
    return (
      <div className={`${styles.wrapper} ${fullWidth ? styles.fullWidth : ''}`}>
        {label && (
          <label htmlFor={props.id} className={styles.label}>
            {label}
          </label>
        )}
        <select
          ref={ref}
          className={`${styles.select} ${error ? styles.error : ''} ${className}`}
          {...props}
        >
          {props.placeholder && (
            <option value="" disabled>
              {props.placeholder}
            </option>
          )}
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        {error && <span className={styles.errorText}>{error}</span>}
      </div>
    );
  }
);

Select.displayName = 'Select';
