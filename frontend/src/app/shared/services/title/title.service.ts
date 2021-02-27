import { Injectable } from "@angular/core";
import { Title } from "@angular/platform-browser";
import { BaseService } from "@shared/services/base.service";
import { LoadingService } from "@shared/services/loading.service";
import { TitleServiceInterface } from "@shared/services/title/title.service-interface";

@Injectable({
  providedIn: "root"
})
export class TitleService extends BaseService implements TitleServiceInterface {
  constructor(public loadingService: LoadingService, public titleService: Title) {
    super(loadingService);
  }

  public setTitle(newTitle: string) {
    this.titleService.setTitle(newTitle + " - AstroBin");
  }
}
