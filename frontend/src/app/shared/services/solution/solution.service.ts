import { Injectable } from "@angular/core";
import { SolutionInterface } from "@shared/interfaces/solution.interface";
import { BaseService } from "@shared/services/base.service";
import { LoadingService } from "@shared/services/loading.service";

@Injectable({
  providedIn: "root"
})
export class SolutionService extends BaseService {
  constructor(public readonly loadingService: LoadingService) {
    super(loadingService);
  }

  getObjectsInField(solution: SolutionInterface): string[] {
    const objects = [];

    if (solution.objects_in_field) {
      solution.objects_in_field.split(",").forEach(object => objects.push(object.trim()));
    }

    // TODO: merge with advanced annotation.

    return objects;
  }
}
