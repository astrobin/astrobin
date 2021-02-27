import { MockBuilder, MockRender } from "ng-mocks";
import { FooterComponent } from "./footer.component";

describe("FooterComponent", () => {
  let component: FooterComponent;

  beforeEach(() => MockBuilder(FooterComponent));
  beforeEach(() => (component = MockRender(FooterComponent).point.componentInstance));

  it("should create", () => {
    expect(component).toBeTruthy();
  });
});
