// tslint:disable:max-classes-per-file

import { AppActionTypes } from "@app/store/actions/app.actions";
import { Action } from "@ngrx/store";
import { ContentTypeInterface } from "@shared/interfaces/content-type.interface";

export class LoadContentType implements Action {
  readonly type = AppActionTypes.LOAD_CONTENT_TYPE;

  constructor(public payload: { appLabel: string; model: string }) {}
}

export class LoadContentTypeSuccess implements Action {
  readonly type = AppActionTypes.LOAD_CONTENT_TYPE_SUCCESS;

  constructor(public payload: ContentTypeInterface) {}
}
