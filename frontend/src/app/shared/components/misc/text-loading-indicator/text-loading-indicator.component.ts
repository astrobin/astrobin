import { Component } from "@angular/core";
import { BaseComponentDirective } from "@shared/components/base-component.directive";

@Component({
  selector: "astrobin-text-loading-indicator",
  templateUrl: "./text-loading-indicator.component.html",
  styleUrls: ["./text-loading-indicator.component.scss"]
})
export class TextLoadingIndicatorComponent extends BaseComponentDirective {}
