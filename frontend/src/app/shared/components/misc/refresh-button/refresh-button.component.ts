import { Component, EventEmitter, OnInit, Output } from "@angular/core";
import { BaseComponentDirective } from "@shared/components/base-component.directive";
import { LoadingService } from "@shared/services/loading.service";

@Component({
  selector: "astrobin-refresh-button",
  templateUrl: "./refresh-button.component.html",
  styleUrls: ["./refresh-button.component.scss"]
})
export class RefreshButtonComponent extends BaseComponentDirective implements OnInit {
  constructor(readonly loadingService: LoadingService) {
    super();
  }

  ngOnInit(): void {}
}
