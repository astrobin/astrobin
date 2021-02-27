import { DomSanitizer } from "@angular/platform-browser";
import { AppModule } from "@app/app.module";
import { NgbActiveModal } from "@ng-bootstrap/ng-bootstrap";
import { MockBuilder, MockRender } from "ng-mocks";
import { LoginModalComponent } from "./login-modal.component";

describe("LoginModalComponent", () => {
  let component: LoginModalComponent;

  beforeEach(() =>
    MockBuilder(LoginModalComponent, AppModule)
      .provide(NgbActiveModal)
      .provide({
        provide: DomSanitizer,
        useValue: {
          sanitize: () => "safeString",
          bypassSecurityTrustHtml: () => "safeString"
        }
      })
  );
  beforeEach(() => (component = MockRender(LoginModalComponent).point.componentInstance));

  it("should create", () => {
    expect(component).toBeTruthy();
  });
});
