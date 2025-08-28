import React from "react";
import styles from "./ToolSelector.module.css";
import {Tool} from "../../../types/home";
import {useStore} from "../../../store/store";

import FinderSelector from "../../../assets/finder/selector.svg";
import CatcherSelector from "../../../assets/contact-catcher/selector.svg";

interface ToolSelectorProps {
    tool: Tool
    onClick: () => void
}

const ToolSelectionModal: React.FC<ToolSelectorProps> = ({tool, onClick}) => {
    const subscription = useStore(s => s.subscription);
    const selectorStyle = {
        "--content-color": subscription!.isSubscriptionExpired() ? "#3C3C3C" : "#7211F8"
    } as React.CSSProperties;

    return (
        <div className={styles.container} onClick={onClick}>
            {tool.id == 'finder' ?
                <FinderSelector height="37px" width="58px" style={selectorStyle}/> :
                <CatcherSelector height="37px" width="58px" style={selectorStyle}/>
            }
            <span className={styles.title}>
                {tool.selectorParts.map((part, index) => (
                    <React.Fragment key={index}>
                        <span>{part}</span>
                        {index < tool.selectorParts.length - 1 && <span className={styles.purple}> // </span>}
                    </React.Fragment>
                ))}
            </span>
        </div>
    );
};

export default ToolSelectionModal;