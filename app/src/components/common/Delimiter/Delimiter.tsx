import styles from "./Delimiter.module.css";
import {ComponentProps, FC} from "react";

interface Props extends ComponentProps<"div"> {}

const Delimiter: FC<Props> = (props) => {
    return <div className={styles.delimiter} {...props}></div>;
};

export default Delimiter;
