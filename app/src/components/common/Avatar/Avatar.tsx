import {CSSProperties, FC, useEffect, useState} from "react";

interface AvatarProps {
    height: string;
    width: string;
    src?: string;
    stub?: string;
    alt?: string;
    className?: string;
    style?: CSSProperties;
}

const Avatar: FC<AvatarProps> = ({height, width, src, stub = "/assets/referral/inactive-user.svg", alt = " ", className, style}) => {
    const [imageSrc, setImageSrc] = useState<string>(src || stub);
    const [hasError, setHasError] = useState(false);

    useEffect(() => {
        if (!src) {
            setImageSrc(stub);
            return;
        }

        setHasError(false);
        setImageSrc(src);
    }, [src, stub]);

    return (
        <img
            height={height}
            width={width}
            src={hasError ? stub : imageSrc}
            alt={alt}
            className={className}
            style={style}
            onError={() => {
                if (!hasError) {
                    setHasError(true);
                }
            }}
        />
    );
};

export default Avatar;
