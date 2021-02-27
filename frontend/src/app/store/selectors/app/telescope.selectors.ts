import { AppState } from "@app/store/reducers/app.reducers";
import { selectApp } from "@app/store/selectors/app/app.selectors";
import { createSelector } from "@ngrx/store";
import { TelescopeInterface } from "@shared/interfaces/telescope.interface";

export const selectTelescopes = createSelector(selectApp, (state: AppState): TelescopeInterface[] => state.telescopes);

export const selectTelescope = createSelector(
  selectTelescopes,
  (telescopes: TelescopeInterface[], pk: number): TelescopeInterface => {
    const matching = telescopes.filter(telescope => telescope.pk === pk);
    return matching.length > 0 ? matching[0] : null;
  }
);
