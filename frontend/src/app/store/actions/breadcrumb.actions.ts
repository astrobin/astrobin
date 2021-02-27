import { AppActionTypes } from "@app/store/actions/app.actions";
import { Action } from "@ngrx/store";
import { BreadcrumbInterface } from "@shared/components/misc/breadcrumb/breadcrumb.interface";

export class SetBreadcrumb implements Action {
  readonly type = AppActionTypes.SET_BREADCRUMB;

  constructor(public payload: { breadcrumb: BreadcrumbInterface[] }) {}
}
