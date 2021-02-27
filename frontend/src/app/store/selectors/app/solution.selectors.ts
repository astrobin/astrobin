import { AppState } from "@app/store/reducers/app.reducers";
import { selectApp } from "@app/store/selectors/app/app.selectors";
import { createSelector } from "@ngrx/store";
import { SolutionInterface } from "@shared/interfaces/solution.interface";

export const selectSolutions = createSelector(selectApp, (state: AppState): SolutionInterface[] => state.solutions);

export const selectSolution = createSelector(
  selectSolutions,
  (solutions: SolutionInterface[], data: { contentType: number; objectId: string }): SolutionInterface => {
    const matching = solutions.filter(
      solution => !!solution && solution.content_type === data.contentType && solution.object_id === data.objectId
    );
    return matching.length > 0 ? matching[0] : null;
  }
);
