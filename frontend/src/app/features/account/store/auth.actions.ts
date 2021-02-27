// tslint:disable:max-classes-per-file

import {
  InitializeAuthSuccessInterface,
  LoginFailureInterface,
  LoginPayloadInterface,
  LoginSuccessInterface
} from "@features/account/store/auth.actions.interfaces";
import { Action } from "@ngrx/store";

export enum AuthActionTypes {
  INITIALIZE = "[Auth] Initialize",
  INITIALIZE_SUCCESS = "[Auth] Initialize success",
  LOGIN = "[Auth] Login",
  LOGIN_SUCCESS = "[Auth] Login success",
  LOGIN_FAILURE = "[Auth] Login failure",
  LOGOUT = "[Auth] Logout"
}

export class InitializeAuth implements Action {
  readonly type = AuthActionTypes.INITIALIZE;
}

export class InitializeAuthSuccess implements Action {
  readonly type = AuthActionTypes.INITIALIZE_SUCCESS;
  constructor(public payload: InitializeAuthSuccessInterface) {}
}

export class Login implements Action {
  readonly type = AuthActionTypes.LOGIN;

  constructor(public payload: LoginPayloadInterface) {}
}

export class LoginSuccess implements Action {
  readonly type = AuthActionTypes.LOGIN_SUCCESS;

  constructor(public payload: LoginSuccessInterface) {}
}

export class LoginFailure implements Action {
  readonly type = AuthActionTypes.LOGIN_FAILURE;

  constructor(public payload: LoginFailureInterface) {}
}

export class Logout implements Action {
  readonly type = AuthActionTypes.LOGOUT;
}

export type All = InitializeAuth | InitializeAuthSuccess | Login | LoginSuccess | LoginFailure | Logout;
