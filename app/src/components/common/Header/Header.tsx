import styles from "./Header.module.css";
import {CSSProperties, FC, ReactElement} from "react";

import {useLocation} from "wouter";

interface HeaderProps {
    height?: number;
    top?: number;
    bottom?: number;
    backTo?: string;
    backoff?: string;
    backStep?: () => boolean;
    icon?: ReactElement | null;
}

const Header: FC<HeaderProps> = ({
    height = 30,
    top = 16,
    bottom = 22,
    backTo = undefined,
    backoff = undefined,
    backStep = undefined,
    icon = <img height="13px" width="167px" src="/assets/header.svg" alt="CARDINAL" />
}) => {
    const [, navigate] = useLocation();

    const handlePageBack = () => {
        if (window.history.state == null) {
            navigate(backoff ? backoff : "/", {replace: true});
        }

        if (window.history.length > 1) {
            window.history.back();
        } else {
            navigate("/", {replace: true});
        }
    };

    const backPage = backTo === "" ? handlePageBack : () => navigate(backTo!, {replace: true});

    const handleBack = () => {
        if (backStep) {
            if (!backStep()) backPage();
        } else {
            backPage();
        }
    };

    return (
        <div
            className={styles.container}
            style={{"--header-height": `${height}px`, "--margin-top": `${top}px`, "--margin-bottom": `${bottom}px`} as CSSProperties}
        >
            {backTo != null && (
                <div className={styles.backButton} onClick={handleBack}>
                    <img height="16px" width="16px" src="/assets/back.svg" alt=" " />
                    Назад
                </div>
            )}
            <div className={styles.header}>{icon}</div>
        </div>
    );
};

export default Header;
