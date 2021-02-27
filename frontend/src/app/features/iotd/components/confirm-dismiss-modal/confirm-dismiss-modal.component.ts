import { Component } from "@angular/core";
import { NgbActiveModal } from "@ng-bootstrap/ng-bootstrap";
import { BaseComponentDirective } from "@shared/components/base-component.directive";

export enum ConfirmDismissResult {
  CANCEL,
  CONFIRM
}

@Component({
  selector: "astrobin-confirm-dismiss-modal",
  templateUrl: "./confirm-dismiss-modal.component.html"
})
export class ConfirmDismissModalComponent extends BaseComponentDirective {
  ConfirmDismissResult = ConfirmDismissResult;

  constructor(public modal: NgbActiveModal) {
    super();
  }
}
