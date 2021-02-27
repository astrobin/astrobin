// tslint:disable:max-classes-per-file

import { AppActionTypes } from "@app/store/actions/app.actions";
import { Action } from "@ngrx/store";
import { ImageThumbnailInterface } from "@shared/interfaces/image-thumbnail.interface";

export class LoadThumbnail implements Action {
  readonly type = AppActionTypes.LOAD_THUMBNAIL;

  constructor(public payload: { id; revision; alias }) {}
}

export class LoadThumbnailSuccess implements Action {
  readonly type = AppActionTypes.LOAD_THUMBNAIL_SUCCESS;

  constructor(public payload: ImageThumbnailInterface) {}
}
