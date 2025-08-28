import React, {ReactElement} from 'react';
import styles from './Header.module.css';
import {useLocation} from "wouter";

interface HeaderProps {
    height?: number;
    backTo?: string;
    icon?: ReactElement
}

const Header: React.FC<HeaderProps> = ({
                                           height = 30,
                                           backTo = undefined,
                                           icon = <img height="13px" width="167px" src="/assets/header.svg" alt="CARDINAL"/>
                                       }) => {
    const [, navigate] = useLocation();

    const handleBack = () => {
        if (window.history.length > 1) {
            window.history.back();
        } else {
            window.location.href = "/";
        }
    };

    return (
        <div className={styles.container} style={{
            "--header-height": `${height}px`
        } as React.CSSProperties}>
            {backTo != null && (
                <div className={styles.backButton} onClick={backTo === "" ? handleBack : () => navigate(backTo)}>
                    <img height="16px" width="16px" src="/assets/back.svg" alt=" "/>
                    Назад
                </div>
            )}
            <div className={styles.header}>
                {icon}
            </div>
        </div>
    );
};

export default Header;
