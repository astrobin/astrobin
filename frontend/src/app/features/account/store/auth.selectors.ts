import { State } from "@app/store/state";
import { AuthState } from "@features/account/store/auth.reducers";
import { createSelector } from "@ngrx/store";

export const selectAuth = (state: State): AuthState => state.auth;
export const selectCurrentUser = createSelector(selectAuth, state => state.user);
export const selectCurrentUserProfile = createSelector(selectAuth, state => state.userProfile);
