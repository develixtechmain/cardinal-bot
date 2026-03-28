import styles from "./ToolSelector.module.css";
import {CSSProperties, FC, Fragment} from "react";

import {useStore} from "../../../store/store";
import {Tool} from "../../../types/home";

import CatcherSelectorOpen from "../../../assets/contact-catcher/selector-open.svg";
import FinderSelectorOpen from "../../../assets/finder/selector-open.svg";

interface ToolSelectorProps {
    tool: Tool;
    onClick: () => void;
}

const ToolSelectionModal: FC<ToolSelectorProps> = ({tool, onClick}) => {
    const subscription = useStore((s) => s.subscription);
    const selectorStyle = {"--content-color": subscription!.isSubscriptionExpired() ? "#3C3C3C" : "#7211F8"} as CSSProperties;

    return (
        <div className={styles.container} onClick={onClick}>
            {tool.id == "finder" ? (
                <FinderSelectorOpen height="37px" width="58px" style={selectorStyle} />
            ) : (
                <CatcherSelectorOpen height="37px" width="58px" style={selectorStyle} />
            )}
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

export default ToolSelectionModal;
