// tslint:disable:max-classes-per-file

import { AppActionTypes } from "@app/store/actions/app.actions";
import { Action } from "@ngrx/store";
import { TelescopeInterface } from "@shared/interfaces/telescope.interface";

export class LoadTelescope implements Action {
  readonly type = AppActionTypes.LOAD_TELESCOPE;

  constructor(public payload: number) {}
}

export class LoadTelescopeSuccess implements Action {
  readonly type = AppActionTypes.LOAD_TELESCOPE_SUCCESS;

  constructor(public payload: TelescopeInterface) {}
}
