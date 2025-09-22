import type {ToolID} from "../utils/consts";

export interface Tool {
    id: ToolID;
    title: string;
    subtitle: string;
    description: string;
    selectorParts: string[];
    url: string;
    color: "purple" | "blue";
}

export interface ActionButton {
    id: string;
    buttonLabel: string;
    color: string;
    colorOpacity?: number;
    expiredColor?: string;
    longColor?: string;
    buttonColor?: string;
    borderColor?: string;
    contentColor?: string;
    url: string;
}
