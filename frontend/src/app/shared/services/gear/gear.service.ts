import { Injectable } from "@angular/core";
import { BaseService } from "@shared/services/base.service";
import { LoadingService } from "@shared/services/loading.service";

@Injectable({
  providedIn: "root"
})
export class GearService extends BaseService {
  constructor(loadingService: LoadingService) {
    super(loadingService);
  }

  getDisplayName(make: string, name: string): string {
    if (!make) {
      return name;
    }

    if (!name) {
      return make;
    }

    if (name.toLowerCase().indexOf(make.toLowerCase()) > -1) {
      return name;
    }

    return `${make.trim()} ${name.trim()}`;
  }
}
