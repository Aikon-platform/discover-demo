import { Icon } from "@iconify/react";
import React from "react";

/*
  A simple useful button with an icon
*/

export function IconBtn(props: { className?:string; icon: string; label?:string; onClick?: (e: React.MouseEvent) => void; disabled?: boolean; }) {
  return (
    <a className={props.className + (props.disabled ? " disabled" : "") + " btn"} href="javascript:void(0)" onClick={props.onClick}>
      <Icon icon={props.icon} />
      {props.label && <span>{props.label}</span>}
    </a>
  );
}