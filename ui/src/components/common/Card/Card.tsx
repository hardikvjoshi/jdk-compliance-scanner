import React from 'react';
import styles from './Card.module.css';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  title?: string;
}

export const Card: React.FC<CardProps> = ({ children, className = '', title, ...props }) => {
  return (
    <div className={`${styles.card} ${className}`} {...props}>
      {title && <h3 className={styles.title}>{title}</h3>}
      {children}
    </div>
  );
};
