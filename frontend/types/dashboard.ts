export interface CausaDetalle {
  rol: string;
  idCausa: string;
  fecha_primer_tramite: string;
  fallo_detectado: string;
  referencia_fallo: string;
  fecha_fallo: string;
  link_fallo: string;
  reclamo_detectado: string;
  fecha_reclamo: string;
  link_reclamo: string;
}

export interface Audiencia {
  fecha: string;
  hora: string;
  rol: string;
  caratula: string;
  tipo_audiencia: string;
  estado: string;
  doc_resolucion: string;
}

export interface CausaResumen {
  tipo: string;
  rol: string;
  fecha_ingreso: string;
  descripcion: string;
  procedimiento: string;
  idcausa: string;
  link: string;
}
