import React from 'react';
import styles from './WideButton.module.css';

interface WideButtonProps {
    color: string;
    text: React.ReactNode;
    textColor?: string;
    onClick?: () => void;
    style?: React.CSSProperties;
    buttonStyle?: React.CSSProperties;
    compact?: boolean;
}

const WideButton: React.FC<WideButtonProps> = ({
                                                   color,
                                                   text,
                                                   textColor = "#FFFFFF",
                                                   onClick,
                                                   style = {},
                                                   buttonStyle = {},
                                                   compact = false
                                               }) => {
    const isDisabled = !onClick;

    return (
        <div className={compact ? styles.compactContainer : styles.wideContainer}
             style={style}>
            <button
                className={`${styles.wideButton} ${isDisabled ? styles.noHover : ''}`}
                onClick={onClick}
                disabled={isDisabled}
                style={{
                    "--button-color": color,
                    "--color": textColor, ...buttonStyle
                } as React.CSSProperties}>
                {text}
            </button>
        </div>
    );
};

export default WideButton;
