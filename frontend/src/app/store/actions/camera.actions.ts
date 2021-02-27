// tslint:disable:max-classes-per-file

import { AppActionTypes } from "@app/store/actions/app.actions";
import { Action } from "@ngrx/store";
import { CameraInterface } from "@shared/interfaces/camera.interface";

export class LoadCamera implements Action {
  readonly type = AppActionTypes.LOAD_CAMERA;

  constructor(public payload: number) {}
}

export class LoadCameraSuccess implements Action {
  readonly type = AppActionTypes.LOAD_CAMERA_SUCCESS;

  constructor(public payload: CameraInterface) {}
}
