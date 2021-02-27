import { Component, OnInit } from "@angular/core";
import { FieldType } from "@ngx-formly/core";

@Component({
  selector: "astrobin-formly-field-ng-select",
  templateUrl: "./formly-field-ng-select.component.html",
  styleUrls: ["./formly-field-ng-select.component.scss"]
})
export class FormlyFieldNgSelectComponent extends FieldType implements OnInit {
  ngOnInit(): void {}
}
