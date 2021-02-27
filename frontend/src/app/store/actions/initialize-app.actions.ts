// tslint:disable:max-classes-per-file

import { AppActionTypes } from "@app/store/actions/app.actions";
import { Action } from "@ngrx/store";
import { BackendConfigInterface } from "@shared/interfaces/backend-config.interface";
import { SubscriptionInterface } from "@shared/interfaces/subscription.interface";

export interface InitializeAppSuccessInterface {
  language: string;
  subscriptions: SubscriptionInterface[];
  backendConfig: BackendConfigInterface;
}

export class InitializeApp implements Action {
  readonly type = AppActionTypes.INITIALIZE;
}

export class InitializeAppSuccess implements Action {
  readonly type = AppActionTypes.INITIALIZE_SUCCESS;

  constructor(public payload: InitializeAppSuccessInterface) {}
}
