import { Injectable } from "@angular/core";
import { environment } from "@env/environment";
import { UserInterface } from "@shared/interfaces/user.interface";
import { BaseService } from "@shared/services/base.service";

const BASE_URL = environment.classicBaseUrl;

@Injectable({
  providedIn: "root"
})
export class ClassicRoutesService extends BaseService {
  HOME = BASE_URL + "/";
  REGISTER = BASE_URL + "/accounts/register/";
  RESET_PASSWORD = BASE_URL + "/accounts/password/reset";
  PRICING = "https://welcome.astrobin.com/pricing";
  UPLOAD = BASE_URL + "/upload/";
  INBOX = BASE_URL + "/messages/inbox/";
  SETTINGS = BASE_URL + "/profile/edit/basic/";
  FORUM_HOME = BASE_URL + "/forum/";
  FORUM_LATEST = BASE_URL + "/forum/topic/latest/";
  FORUM_SUBSCRIBED = BASE_URL + "/forum/topic/subscribed";
  SEARCH = BASE_URL + "/search/";
  TOP_PICK_NOMINATIONS = BASE_URL + "/explore/top-pick-nominations/";
  TOP_PICKS = BASE_URL + "/explore/top-picks/";
  IOTD = BASE_URL + "/iotd/archive/";
  GROUPS = BASE_URL + "/groups/";
  REMOTE_ASTROPHOTOGRAPHY = "https://welcome.astrobin.com/remote-astrophotography";
  ASTROPHOTOGRAPHERS_LIST = BASE_URL + "/astrophotographers-list/";
  CONTRIBUTORS_LIST = BASE_URL + "/contributors-list/";
  ABOUT = "https://welcome.astrobin.com/about";
  FAQ = "https://welcome.astrobin.com/faq";
  HELP_API = "https://welcome.astrobin.com/application-programming-interface";
  SPONSORS = "https://welcome.astrobin.com/sponsors-and-partners";
  CONTACT = BASE_URL + "/contact/";
  MODERATE_IMAGE_QUEUE = BASE_URL + "/moderate/images/";
  MODERATE_SPAM_QUEUE = BASE_URL + "/moderate/images/spam/";
  IOTD_JUDGEMENT_QUEUE = BASE_URL + "/iotd/judgement-queue/";
  NOTIFICATION_SETTINGS = BASE_URL + "/notifications/settings/";

  COMMERCIAL_PRODUCTS = (profile: UserInterface) => BASE_URL + `/users/${profile?.username}/commercial/products/`;

  GALLERY = (profile: UserInterface) => BASE_URL + `/users/${profile?.username}/`;

  STAGING_GALLERY = (profile: UserInterface) => BASE_URL + `/users/${profile?.username}/?staging`;

  BOOKMARKS = (profile: UserInterface) => BASE_URL + `/users/${profile?.username}/bookmarks/`;

  PLOTS = (profile: UserInterface) => BASE_URL + `/users/${profile?.username}/plots/`;

  API_KEYS = (profile: UserInterface) => BASE_URL + `/users/${profile?.username}/apikeys/`;

  SET_LANGUAGE = (languageCode: string, next) => BASE_URL + `/language/set/${languageCode}/?next=${next}`;

  IMAGE = (id: string) => BASE_URL + `/${id}/`;

  EDIT_IMAGE_THUMBNAILS = (id: string) => BASE_URL + `/edit/thumbnails/${id}/`;

  EDIT_IMAGE_REVISION = (id: string) => BASE_URL + `/edit/revision/${id}/`;
}
