// tslint:disable:max-classes-per-file

import { AppActionTypes } from "@app/store/actions/app.actions";
import { Action } from "@ngrx/store";

export class ShowFullscreenImage implements Action {
  readonly type = AppActionTypes.SHOW_FULLSCREEN_IMAGE;

  constructor(public payload: number) {}
}

export class HideFullscreenImage implements Action {
  readonly type = AppActionTypes.HIDE_FULLSCREEN_IMAGE;
}
