import { Component, Input, OnInit } from "@angular/core";
import { LoadCamera } from "@app/store/actions/camera.actions";
import { State } from "@app/store/state";
import { Store } from "@ngrx/store";
import { BaseComponentDirective } from "@shared/components/base-component.directive";
import { CameraInterface } from "@shared/interfaces/camera.interface";
import { GearService } from "@shared/services/gear/gear.service";
import { Observable } from "rxjs";

@Component({
  selector: "astrobin-camera",
  templateUrl: "./camera.component.html",
  styleUrls: ["./camera.component.scss"]
})
export class CameraComponent extends BaseComponentDirective implements OnInit {
  camera$: Observable<CameraInterface>;

  @Input()
  id: number;

  constructor(public readonly store$: Store<State>, public readonly gearService: GearService) {
    super();
  }

  ngOnInit(): void {
    if (this.id === undefined) {
      throw new Error("Attribute 'id' is required");
    }

    this.camera$ = this.store$.select(state => {
      const cameras = state.app.cameras.filter(camera => camera.pk === this.id);
      return cameras.length > 0 ? cameras[0] : null;
    });

    this.store$.dispatch(new LoadCamera(this.id));
  }
}
