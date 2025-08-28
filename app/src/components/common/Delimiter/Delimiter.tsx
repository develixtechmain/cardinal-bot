import React, {ComponentProps} from 'react';
import styles from './Delimiter.module.css';

interface Props extends ComponentProps<"div"> {
}

const Delimiter: React.FC<Props> = (props) => {
    return <div className={styles.delimiter} {...props}></div>;
};

export default Delimiter;
