import styles from "./ToolCard.module.css";
import {CSSProperties, FC, Fragment} from "react";

import {useLocation} from "wouter";

import {Tool} from "../../../types/home";

import CatcherSelector from "../../../assets/contact-catcher/selector.svg";
import FinderSelector from "../../../assets/finder/selector.svg";

interface ToolCardProps {
    tool: Tool;
    currentToolId: string;
    onClose: () => void;
}

export const ToolCard: FC<ToolCardProps> = ({tool, currentToolId, onClose}) => {
    const [, navigate] = useLocation();

    const logo =
        tool.id == "finder" ? (
            <FinderSelector height="37px" width="58px" style={{"--content-color": "#7211F8"} as CSSProperties} />
        ) : (
            <CatcherSelector height="37px" width="58px" style={{"--content-color": "#898989"} as CSSProperties} />
        );

    return (
        <div
            className={`${styles.container} ${tool.id === currentToolId ? styles.selected : ""}`}
            onClick={() => {
                if (currentToolId === tool.id) onClose();
                else navigate(tool.url);
            }}
        >
            {logo}
            <span className={styles.title}>
                {tool.selectorParts.map((part, index) => (
                    <Fragment key={index}>
                        <span>{part}</span>
                        {index < tool.selectorParts.length - 1 && <span className={styles.purple}> // </span>}
                    </Fragment>
                ))}
            </span>
        </div>
    );
};
