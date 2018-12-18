import { HttpClient } from "@angular/common/http";
import { HttpClientTestingModule } from "@angular/common/http/testing";
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { TranslateLoader, TranslateModule } from "@ngx-translate/core";
import { HttpLoaderFactory } from "../../../app.module";
import { UserModel } from "../../models/common/user.model";
import { UserProfileModel } from "../../models/common/userprofile.model";
import { PipesModule } from "../../pipes/pipes.module";
import { AppContextService, IAppContext } from "../../services/app-context.service";
import { SharedModule } from "../../shared.module";
import { HeaderComponent } from './header.component';

class MockAppContextService {
  get = jasmine.createSpy("get").and.returnValue({
    currentUserProfile: new UserProfileModel({
        userObject: new UserModel({})
      }
    )
  } as IAppContext);
}
describe('HeaderComponent', () => {
  let component: HeaderComponent;
  let fixture: ComponentFixture<HeaderComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      imports: [
        HttpClientTestingModule,
        TranslateModule.forRoot({
          loader: {
            provide: TranslateLoader,
            useFactory: HttpLoaderFactory,
            deps: [HttpClient]
          }
        }),
        SharedModule,
        PipesModule
      ],
      providers: [
        { provide: AppContextService, useClass: MockAppContextService }
      ],
      declarations: [HeaderComponent]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(HeaderComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
