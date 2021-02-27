import { Component } from "@angular/core";
import { BaseComponentDirective } from "@shared/components/base-component.directive";

@Component({
  selector: "astrobin-empty-list",
  templateUrl: "./empty-list.component.html",
  styleUrls: ["./empty-list.component.scss"]
})
export class EmptyListComponent extends BaseComponentDirective {}
